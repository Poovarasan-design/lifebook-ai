import re
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from app.models.commitment import Commitment
from app.models.diary import DiaryEntry
from app.models.notification import Notification
from app.models.entity import Entity
from app.schemas.search import ForgettingResponse, ForgettingItem
from app.services.notification_service import notification_service

class CommitmentService:
    @staticmethod
    def parse_temporal_due_date(text: str, base_dt: Optional[datetime] = None) -> Tuple[Optional[datetime], str, bool]:
        """
        Parses relative dates (today, tomorrow, next monday, in N days, etc.)
        and time expressions (8:14pm, 10 AM, 20:14) into:
        (resolved_dt, due_label, is_past)
        """
        if not base_dt:
            base_dt = datetime.now(timezone.utc)
        elif base_dt.tzinfo is None:
            base_dt = base_dt.replace(tzinfo=timezone.utc)

        lower = text.lower()
        now = datetime.now(timezone.utc)

        # 1. Parse Time of Day (e.g., 8:14pm, 8:14 PM, 8.14pm, 20:14, 10 AM, 8pm)
        hour = None
        minute = 0
        time_display = None

        m_time_hm = re.search(r'\b(?:at\s+)?(\d{1,2})(?::|\.)(\d{2})\s*(am|pm)?\b', text, re.I)
        if m_time_hm:
            h_raw = int(m_time_hm.group(1))
            m_raw = int(m_time_hm.group(2))
            ampm = (m_time_hm.group(3) or '').lower()
            if ampm == 'pm' and h_raw < 12:
                h_raw += 12
            elif ampm == 'am' and h_raw == 12:
                h_raw = 0
            if 0 <= h_raw <= 23 and 0 <= m_raw <= 59:
                hour = h_raw
                minute = m_raw
                disp_h = hour % 12 or 12
                tag = 'PM' if hour >= 12 else 'AM'
                time_display = f"{disp_h}:{minute:02d} {tag}"
        else:
            m_time_h = re.search(r'\b(?:at\s+)?(\d{1,2})\s*(am|pm)\b', text, re.I)
            if m_time_h:
                h_raw = int(m_time_h.group(1))
                ampm = m_time_h.group(2).lower()
                if ampm == 'pm' and h_raw < 12:
                    h_raw += 12
                elif ampm == 'am' and h_raw == 12:
                    h_raw = 0
                if 0 <= h_raw <= 23:
                    hour = h_raw
                    minute = 0
                    disp_h = hour % 12 or 12
                    tag = 'PM' if hour >= 12 else 'AM'
                    time_display = f"{disp_h}:00 {tag}"

        # 2. Parse Date Component
        target_date = None
        base_label = "Upcoming"
        is_past = False

        weekday_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2,
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
        }

        m_after_days = re.search(r'(?:after|in)\s+(\d+)\s+days?', lower)
        m_after_weeks = re.search(r'(?:after|in)\s+(\d+)\s+weeks?', lower)

        if "yesterday" in lower:
            target_date = base_dt.date() - timedelta(days=1)
            base_label = "Yesterday"
            is_past = True
        elif "today" in lower or "tonight" in lower:
            target_date = base_dt.date()
            base_label = "Today"
        elif "day after tomorrow" in lower:
            target_date = base_dt.date() + timedelta(days=2)
            base_label = f"Day after tomorrow ({target_date.strftime('%B %d')})"
        elif "tomorrow" in lower or "tmrw" in lower:
            target_date = base_dt.date() + timedelta(days=1)
            base_label = f"Tomorrow ({target_date.strftime('%B %d')})"
        elif m_after_days:
            days_offset = int(m_after_days.group(1))
            target_date = base_dt.date() + timedelta(days=days_offset)
            base_label = f"In {days_offset} days ({target_date.strftime('%B %d')})"
        elif m_after_weeks:
            weeks_offset = int(m_after_weeks.group(1))
            target_date = base_dt.date() + timedelta(weeks=weeks_offset)
            base_label = f"In {weeks_offset} weeks ({target_date.strftime('%B %d')})"
        elif "next week" in lower:
            target_date = base_dt.date() + timedelta(days=7)
            base_label = f"Next week ({target_date.strftime('%B %d')})"
        else:
            # Check for weekday references
            matched_weekday = None
            for w_name, w_idx in weekday_map.items():
                if re.search(rf'\b(?:next|this|on|by)?\s*{w_name}\b', lower):
                    matched_weekday = (w_name, w_idx)
                    break

            if matched_weekday:
                w_name, w_idx = matched_weekday
                days_ahead = (w_idx - base_dt.weekday()) % 7
                if f"next {w_name}" in lower or days_ahead == 0:
                    days_ahead = days_ahead + 7 if (f"next {w_name}" in lower or days_ahead == 0) else days_ahead
                target_date = base_dt.date() + timedelta(days=days_ahead)
                prefix = "Next " if f"next {w_name}" in lower else ""
                base_label = f"{prefix}{w_name.capitalize()} ({target_date.strftime('%B %d')})"

        # Default fallback date if only time was specified (e.g. "at 8:14pm meeting")
        if not target_date and hour is not None:
            target_date = base_dt.date()
            base_label = "Today"

        # 3. Combine Date and Time into resolved UTC datetime
        resolved_dt = None
        if target_date:
            h_final = hour if hour is not None else 18
            m_final = minute if hour is not None else 0
            resolved_dt = datetime(
                target_date.year, target_date.month, target_date.day,
                h_final, m_final, tzinfo=timezone.utc
            )

        # Format final human label
        if time_display:
            if base_label == "Today":
                due_label = f"Today, {time_display}"
            elif "Tomorrow" in base_label:
                due_label = f"Tomorrow, {time_display}"
            elif base_label != "Upcoming":
                due_label = f"{base_label} at {time_display}"
            else:
                due_label = f"{time_display}"
        else:
            due_label = base_label

        return resolved_dt, due_label, is_past

    @classmethod
    def extract_tasks_from_text(cls, raw: str) -> List[str]:
        """
        Extracts actionable commitment and event titles from natural language memory text.
        """
        extracted_tasks = []

        # Pattern 1: I have a/an <event> or have a/an <event>
        # e.g. "Today 8:14pm I have a google meeting", "Tomorrow at 10 AM I have an association function"
        m_have = re.search(
            r'\b(?:i\s+)?have\s+(?:a|an)\s+([A-Za-z0-9\s_-]+?)(?:\s+(?:at|with|by|on|tomorrow|today|tonight|next|\.|\,|$)|$)',
            raw,
            re.IGNORECASE
        )
        if m_have:
            cand = m_have.group(1).strip()
            cand = re.sub(
                r'\s+(?:today|tomorrow|tonight|next\s+\w+|on\s+\w+|by\s+\w+|\d{1,2}(?::|\.)\d{2}|\d{1,2}\s*(?:am|pm)).*$',
                '',
                cand,
                flags=re.IGNORECASE
            ).strip()
            if len(cand) > 2 and cand.lower() not in ['good', 'great', 'bad', 'nice', 'wonderful', 'lot', 'busy day']:
                extracted_tasks.append(cand.title())

        # Pattern 2: need to / have to / must / plan to / promised to / promise to / supposed to / decided to
        # e.g. "Next Monday I need to submit the project", "I promised to send the REST API schema"
        m_promise = re.search(
            r'\b(?:promised to|promise to|need to|have to|must|plan to|supposed to|decided to)\s+([^.,;\n]+)',
            raw,
            re.IGNORECASE
        )
        if m_promise:
            task_clean = m_promise.group(1).strip()
            task_clean = re.sub(
                r'\s+(?:by|on|at|before)\s+(?:friday|monday|tuesday|wednesday|thursday|saturday|sunday|tomorrow|today|tonight|next week|\d{1,2}(?::|\.)\d{2}|\d{1,2}\s*(?:am|pm)).*$',
                '',
                task_clean,
                flags=re.IGNORECASE
            ).strip()
            if len(task_clean) > 2 and not any(t.lower() == task_clean.lower() for t in extracted_tasks):
                extracted_tasks.append(task_clean.capitalize())

        # Pattern 3: explicit action verbs: call, send, finish, submit, complete, attend, prepare, review, pay, book
        m_act = re.search(
            r'\b(call|send|finish|submit|complete|attend|prepare|review|pay|book|schedule)\s+([^.,;\n]+)',
            raw,
            re.IGNORECASE
        )
        if m_act:
            verb = m_act.group(1).capitalize()
            rest = m_act.group(2).strip()
            rest = re.sub(
                r'\s+(?:by|on|at|before)\s+(?:friday|monday|tuesday|wednesday|thursday|saturday|sunday|tomorrow|today|tonight|next week|\d{1,2}(?::|\.)\d{2}|\d{1,2}\s*(?:am|pm)).*$',
                '',
                rest,
                flags=re.IGNORECASE
            ).strip()
            candidate = f"{verb} {rest}".strip()
            if len(rest) > 1 and not any(candidate.lower() in t.lower() for t in extracted_tasks):
                extracted_tasks.append(candidate)

        # Pattern 4: follow up with <someone>
        m_follow = re.search(r'\bfollow\s+up\s+with\s+([A-Za-z\s]+?)(?:\s+(?:by|on|tomorrow|\.|$)|$)', raw, re.IGNORECASE)
        if m_follow and not any("follow" in t.lower() for t in extracted_tasks):
            extracted_tasks.append(f"Follow up with {m_follow.group(1).strip()}".title())

        return extracted_tasks

    @staticmethod
    def extract_and_save_commitments(entry: DiaryEntry, db: Session) -> List[Commitment]:
        raw = f"{entry.raw_text or ''} {entry.transcript or ''} {entry.generated_content or ''}"
        
        base_dt = entry.entry_date or entry.created_at
        if not base_dt:
            base_dt = datetime.now(timezone.utc)
        elif base_dt.tzinfo is None:
            base_dt = base_dt.replace(tzinfo=timezone.utc)

        # Detect person / thread target from existing extracted entities or capitalized names
        entry_entities = db.query(Entity).filter(Entity.diary_entry_id == entry.id, Entity.type == "person").all()
        person_name = entry_entities[0].name if entry_entities else None

        if not person_name:
            m_person = re.search(r"\b(?:with|and|to)\s+([A-Z][a-z]+)\b", raw)
            if m_person and m_person.group(1) not in ["Today", "Yesterday", "Tomorrow", "The", "My", "Google", "Zoom"]:
                person_name = m_person.group(1)

        # 1. Parse temporal due date and time
        target_dt, due_label, is_past = CommitmentService.parse_temporal_due_date(raw, base_dt)

        # 2. Extract actionable tasks/events
        extracted_tasks = CommitmentService.extract_tasks_from_text(raw)
        
        # If the text explicitly describes a completed past event without any action commitment, skip
        if is_past and not extracted_tasks:
            return []

        created_commitments: List[Commitment] = []

        for task in extracted_tasks:
            # Check duplicate for this entry or this user with identical task description
            existing = db.query(Commitment).filter(
                Commitment.user_id == entry.user_id,
                (Commitment.diary_entry_id == entry.id) | (Commitment.description.ilike(f"%{task[:30]}%"))
            ).first()

            thread_name = f"{person_name} - Collaboration" if person_name else "Personal Commitments"
            next_act = f"{task} ({due_label})" if due_label != "Upcoming" else task

            if existing:
                # Update existing commitment details without duplicating
                existing.resolved_due_date = target_dt or existing.resolved_due_date
                existing.due_date = due_label or existing.due_date
                existing.next_action = next_act[:150]
                created_commitments.append(existing)
            else:
                new_comm = Commitment(
                    user_id=entry.user_id,
                    diary_entry_id=entry.id,
                    description=task[:120],
                    project=f"{person_name} Collaboration" if person_name else "Personal Action Item",
                    due_date=due_label,
                    resolved_due_date=target_dt,
                    priority="high",
                    status="PENDING",
                    confidence=0.94,
                    activity_thread=thread_name,
                    next_action=next_act[:150]
                )
                db.add(new_comm)
                created_commitments.append(new_comm)

        if created_commitments:
            db.commit()
            # 3. Synchronize with reminder notification lifecycle
            try:
                notification_service.sync_reminders(entry.user_id, db)
            except Exception:
                pass

        return created_commitments

    @staticmethod
    def get_user_commitments(user_id: str, status: Optional[str], db: Session) -> List[Commitment]:
        q = db.query(Commitment).filter(Commitment.user_id == user_id)
        if status:
            q = q.filter(Commitment.status == status.upper())
        return q.order_by(Commitment.created_at.desc()).all()

    @staticmethod
    def get_forgetting_commitments(user_id: str, db: Session) -> ForgettingResponse:
        now = datetime.now(timezone.utc)
        items = db.query(Commitment).filter(
            Commitment.user_id == user_id,
            Commitment.status == "PENDING"
        ).order_by(Commitment.priority.desc(), Commitment.created_at.desc()).all()

        res_items = []
        for c in items:
            days_ago = 0
            if c.created_at:
                c_dt = c.created_at if c.created_at.tzinfo else c.created_at.replace(tzinfo=timezone.utc)
                days_ago = max(0, (now - c_dt).days)

            if c.due_date and c.due_date != "Upcoming":
                reason = f"Action item with due date '{c.due_date}' recorded in your memories"
            elif c.priority == "high":
                reason = "High-priority commitment pending completion"
            else:
                reason = "Pending task logged in your personal journal"

            res_items.append(ForgettingItem(
                id=c.id,
                title=c.description,
                description=f"Project / Focus: {c.project or 'Personal'}",
                due_date=c.due_date or "Upcoming",
                priority=c.priority or "high",
                source_entry_id=c.diary_entry_id,
                days_ago_mentioned=days_ago,
                reason=reason
            ))

        headline = f"You have {len(res_items)} action items worth checking:" if res_items else "You are completely caught up with your commitments!"
        return ForgettingResponse(
            headline=headline,
            items=res_items
        )

commitment_service = CommitmentService()

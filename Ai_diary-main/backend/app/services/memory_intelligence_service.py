"""
Memory Intelligence Service — Phase 3 Task 5

Provides the next intelligence layer for user memories:
1. Memory Importance Scoring (Deterministic, content/metadata grounded)
2. Routine & Habit Detection (Requires >=2 occurrences across distinct memories)
3. Routine Deviation Detection (Identifies changes in established routines without hallucinations)
4. Memory Connections & Life Graph Sync (Deduplicated graph node and edge creation)
5. Forgetting & Smart Life Insights (Unresolved commitments, upcoming dates, deviations)
6. Strict User Isolation on all queries
"""

from __future__ import annotations
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.diary import DiaryEntry
from app.models.entity import Entity
from app.models.commitment import Commitment
from app.models.routine import Routine
from app.models.life_graph import LifeGraphRelationship


class MemoryIntelligenceService:
    # -----------------------------------------------------------------------
    # 1. MEMORY IMPORTANCE SCORING
    # -----------------------------------------------------------------------
    @staticmethod
    def compute_memory_importance(
        entry: DiaryEntry,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Compute a deterministic importance score (0.0 to 1.0) grounded strictly
        in available memory content, extracted entities, and commitments.

        Signals:
        - Commitments (pending/high-priority, deadlines) : up to +0.35
        - Named Projects & Collaborators                 : up to +0.30
        - Milestone / Achievement / Future date keywords : up to +0.25
        - Content substance (length, photos)             : up to +0.10
        """
        text = f"{entry.title or ''} {entry.raw_text or ''} {entry.generated_content or ''}"
        text_lower = text.lower()
        signals: List[str] = []
        score = 0.15  # Baseline baseline for any recorded memory

        # --- Signal 1: Commitments ---
        commitments: List[Commitment] = []
        if db is not None:
            commitments = db.query(Commitment).filter(
                Commitment.diary_entry_id == entry.id,
                Commitment.user_id == entry.user_id
            ).all()

        if commitments:
            score += 0.15
            signals.append("contains_commitments")
            high_pri = [c for c in commitments if c.priority == "high"]
            if high_pri:
                score += 0.10
                signals.append("high_priority_commitment")
            has_deadlines = [c for c in commitments if c.due_date and c.due_date != "Upcoming"]
            if has_deadlines:
                score += 0.05
                signals.append("explicit_deadline")
        else:
            # Fallback text check for action commitments
            if re.search(r"\b(?:promised to|need to|plan to|have to|deadline|due by)\b", text_lower):
                score += 0.10
                signals.append("commitment_indicated")

        # --- Signal 2: Named Projects & People Entities ---
        entities: List[Entity] = []
        if db is not None:
            entities = db.query(Entity).filter(
                Entity.diary_entry_id == entry.id,
                Entity.user_id == entry.user_id
            ).all()

        projects = [e for e in entities if e.type == "project"]
        people = [e for e in entities if e.type == "person"]

        if projects:
            score += 0.15
            signals.append(f"project:{projects[0].name}")
        elif "hackathon" in text_lower or "sprint" in text_lower or "project" in text_lower:
            score += 0.10
            signals.append("project_work")

        if people:
            score += 0.10
            signals.append(f"collaborators:{len(people)}")
        elif re.search(r"\b(?:with|met|collaborated with)\s+[A-Z][a-z]+\b", text):
            score += 0.05
            signals.append("social_connection")

        # --- Signal 3: Milestone / Achievement Keywords ---
        milestone_keywords = [
            "milestone", "achieved", "completed", "launched", "won", "award",
            "signed", "breakthrough", "finalized", "first time", "celebrat"
        ]
        if any(w in text_lower for w in milestone_keywords):
            score += 0.15
            signals.append("milestone_achievement")

        # Future appointment / event
        future_keywords = ["tomorrow", "next week", "scheduled", "appointment", "presentation"]
        if any(w in text_lower for w in future_keywords):
            score += 0.08
            signals.append("future_event")

        # --- Signal 4: Content Substance ---
        if len(text.strip()) > 300:
            score += 0.05
            signals.append("detailed_narrative")
        if entry.photo_urls and len(entry.photo_urls) > 0:
            score += 0.05
            signals.append("visual_memory")

        # Bound score between 0.0 and 1.0
        final_score = round(min(1.0, max(0.0, score)), 2)

        if final_score >= 0.70:
            level = "high"
        elif final_score >= 0.40:
            level = "medium"
        else:
            level = "low"

        return {
            "importance_score": final_score,
            "level": level,
            "signals": signals
        }

    # -----------------------------------------------------------------------
    # 2. ROUTINE & HABIT DETECTION (Requires >= min_occurrences history)
    # -----------------------------------------------------------------------
    @staticmethod
    def detect_user_routines(
        user_id: str,
        db: Session,
        min_occurrences: int = 2
    ) -> List[Routine]:
        """
        Scans confirmed memories for recurring patterns.
        Strict rule: requires >= min_occurrences (default 2) across distinct memories
        before identifying/creating a Routine record. Never creates routines from a single memory.
        """
        # Fetch confirmed diary entries for the user
        entries = db.query(DiaryEntry).filter(
            DiaryEntry.user_id == user_id,
            DiaryEntry.status.in_(["CONFIRMED", "COMPLETED", "GRAPH_UPDATED", "INDEXED"])
        ).order_by(DiaryEntry.entry_date.asc()).all()

        if len(entries) < min_occurrences:
            return []

        # Activity pattern buckets: (activity_canonical_name, weekday_name) -> list of entries
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        pattern_clusters: Dict[tuple, List[DiaryEntry]] = defaultdict(list)

        for entry in entries:
            dt = entry.entry_date or entry.created_at
            if not dt:
                continue
            day_name = weekday_names[dt.weekday()]
            content_lower = f"{entry.title or ''} {entry.raw_text or ''} {entry.generated_content or ''}".lower()

            # Pattern 1: Workout / Gym / Yoga / Exercise
            if any(w in content_lower for w in ["gym", "workout", "cardio", "weight lifting", "yoga", "exercise", "jogging"]):
                pattern_clusters[("Workout & Fitness", day_name)].append(entry)

            # Pattern 2: Sprint / Hackathon / Coding / Project Work
            if any(w in content_lower for w in ["hackathon", "sprint", "coding sprint", "standup", "review sprint"]):
                pattern_clusters[("Project Sprint", day_name)].append(entry)

            # Pattern 3: Dining Out / Weekly Lunch / Cafe
            if any(w in content_lower for w in ["lunch", "restaurant", "cafe", "dinner with"]):
                # Extract specific place if available
                place_match = re.search(r"(?:at|in)\s+([A-Z][a-zA-Z\s]{2,20})", entry.raw_text or entry.generated_content or "")
                place_name = place_match.group(1).strip() if place_match else "Local Cafe"
                pattern_clusters[(f"Dining at {place_name}", day_name)].append(entry)

            # Pattern 4: Sketching / Art / Creative Flow
            if any(w in content_lower for w in ["sketch", "watercolor", "painting", "art session"]):
                pattern_clusters[("Creative Sketching", day_name)].append(entry)

            # Pattern 5: Study / Reading
            if any(w in content_lower for w in ["reading", "study session", "library", "book club"]):
                pattern_clusters[("Study & Reading", day_name)].append(entry)

        detected_routines: List[Routine] = []

        for (activity_name, day_name), matched_entries in pattern_clusters.items():
            # Deduplicate by distinct dates
            distinct_dates = {e.entry_date.date() for e in matched_entries if e.entry_date}
            count = len(distinct_dates) if distinct_dates else len(matched_entries)

            # STRICT GUARD: only detect when enough historical evidence exists
            if count < min_occurrences:
                continue

            latest_entry = matched_entries[-1]
            last_observed_dt = latest_entry.entry_date or latest_entry.created_at or datetime.now(timezone.utc)
            title = f"{day_name} {activity_name}"

            # Check if routine already exists in DB
            existing_routine = db.query(Routine).filter(
                Routine.user_id == user_id,
                Routine.pattern == day_name,
                Routine.activity == activity_name
            ).first()

            if existing_routine:
                existing_routine.occurrence_count = count
                existing_routine.last_observed = last_observed_dt
                existing_routine.confidence = min(0.98, round(0.70 + (count * 0.05), 2))
                existing_routine.is_active = True
                detected_routines.append(existing_routine)
            else:
                new_routine = Routine(
                    user_id=user_id,
                    title=title,
                    activity=activity_name,
                    pattern=day_name,
                    frequency="weekly",
                    occurrence_count=count,
                    confidence=min(0.98, round(0.70 + (count * 0.05), 2)),
                    last_observed=last_observed_dt,
                    is_active=True,
                    deviation_active=False
                )
                db.add(new_routine)
                detected_routines.append(new_routine)

        db.commit()
        return detected_routines

    # -----------------------------------------------------------------------
    # 3. ROUTINE DEVIATION DETECTION
    # -----------------------------------------------------------------------
    @staticmethod
    def check_routine_deviations(
        user_id: str,
        db: Session
    ) -> List[Routine]:
        """
        Detects when an established routine (occurrence_count >= 2) had a missed or altered habit
        based on the user's latest recorded diary entry for that day of week.
        """
        routines = db.query(Routine).filter(
            Routine.user_id == user_id,
            Routine.is_active == True,
            Routine.occurrence_count >= 2
        ).all()

        if not routines:
            return []

        # Get the most recent 10 confirmed diary entries
        recent_entries = db.query(DiaryEntry).filter(
            DiaryEntry.user_id == user_id,
            DiaryEntry.status.in_(["CONFIRMED", "COMPLETED", "INDEXED"])
        ).order_by(DiaryEntry.entry_date.desc()).limit(10).all()

        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        deviated_routines: List[Routine] = []

        for routine in routines:
            # Find the most recent entry that matches this routine's weekday
            matching_day_entries = [
                e for e in recent_entries
                if e.entry_date and weekday_names[e.entry_date.weekday()] == routine.pattern
            ]

            if not matching_day_entries:
                continue

            latest_day_entry = matching_day_entries[0]
            entry_text = f"{latest_day_entry.title or ''} {latest_day_entry.raw_text or ''} {latest_day_entry.generated_content or ''}".lower()

            # Check if the expected activity appears in this entry
            activity_keywords = [w.lower() for w in routine.activity.split() if len(w) > 3]
            activity_found = any(kw in entry_text for kw in activity_keywords)

            if not activity_found:
                # Deviation detected!
                routine.deviation_active = True
                routine.deviation_prompt = (
                    f"Usually on {routine.pattern}s you log '{routine.activity}', "
                    f"but on {latest_day_entry.entry_date.strftime('%B %d')} you recorded '{latest_day_entry.title or 'a different activity'}'."
                )
                deviated_routines.append(routine)
            else:
                routine.deviation_active = False
                routine.deviation_prompt = None

        db.commit()
        return [r for r in routines if r.deviation_active]

    # -----------------------------------------------------------------------
    # 4. MEMORY CONNECTIONS & LIFE GRAPH DEDUPLICATION
    # -----------------------------------------------------------------------
    @staticmethod
    def sync_entry_to_graph_deduped(entry: DiaryEntry, db: Session):
        """
        Synchronizes extracted entities, projects, places, activities, and commitments to the Life Graph
        with STRICT deduplication to avoid redundant graph nodes or edges.
        """
        user_id = entry.user_id

        # 1. Clean existing relationships for this specific diary entry to prevent duplicates on edit/reconfirm
        db.query(LifeGraphRelationship).filter(
            LifeGraphRelationship.user_id == user_id,
            LifeGraphRelationship.diary_entry_id == entry.id
        ).delete()

        entities = db.query(Entity).filter(
            Entity.diary_entry_id == entry.id,
            Entity.user_id == user_id
        ).all()

        people = [e for e in entities if e.type == "person"]
        places = [e for e in entities if e.type == "place"]
        projects = [e for e in entities if e.type == "project"]
        activities = [e for e in entities if e.type == "activity"]
        commitments = db.query(Commitment).filter(
            Commitment.diary_entry_id == entry.id,
            Commitment.user_id == user_id
        ).all()

        entry_title = (entry.title or "Memory").strip()
        entry_date_str = entry.entry_date.isoformat() if entry.entry_date else None

        def _add_edge_if_new(
            source_type: str, source_name: str,
            target_type: str, target_name: str,
            rel_type: str, confidence: float = 0.95,
            extra_meta: Optional[Dict[str, Any]] = None
        ):
            s_name = source_name.strip()
            t_name = target_name.strip()
            if not s_name or not t_name:
                return

            meta = {
                "entry_id": entry.id,
                "entry_title": entry_title,
                "entry_date": entry_date_str
            }
            if extra_meta:
                meta.update(extra_meta)

            # Check if this exact relationship already exists for this user
            existing = db.query(LifeGraphRelationship).filter(
                LifeGraphRelationship.user_id == user_id,
                LifeGraphRelationship.source_name == s_name,
                LifeGraphRelationship.target_name == t_name,
                LifeGraphRelationship.relationship_type == rel_type
            ).first()

            if not existing:
                db.add(LifeGraphRelationship(
                    user_id=user_id,
                    diary_entry_id=entry.id,
                    source_type=source_type,
                    source_name=s_name,
                    target_type=target_type,
                    target_name=t_name,
                    relationship_type=rel_type,
                    confidence=confidence,
                    metadata_info=meta
                ))
            else:
                # Update existing record's metadata and freshness
                existing.confidence = max(existing.confidence or 0.9, confidence)
                existing.metadata_info = meta

        # 1. User Root Edges
        for p in people:
            _add_edge_if_new("User", "You", "Person", p.name, "met", p.confidence)
        for pl in places:
            _add_edge_if_new("User", "You", "Place", pl.name, "visited", pl.confidence)
        for proj in projects:
            _add_edge_if_new("User", "You", "Project", proj.name, "worked_on", proj.confidence)
        for ac in activities:
            _add_edge_if_new("User", "You", "Activity", ac.name, "engaged_in", ac.confidence)

        # 2. Person Relationships (Person ↔ Memory, Person ↔ Project, Person ↔ Place, Person ↔ Commitment)
        for p in people:
            _add_edge_if_new("Person", p.name, "Memory", entry_title, "appears_in", p.confidence)
            for proj in projects:
                _add_edge_if_new("Person", p.name, "Project", proj.name, "collaborated_on", 0.95)
            for pl in places:
                _add_edge_if_new("Person", p.name, "Place", pl.name, "visited_with", 0.90)
            for comm in commitments:
                _add_edge_if_new("Person", p.name, "Commitment", comm.description[:80], "involved_in", 0.90)

        # 3. Project Relationships (Project ↔ Memory, Project ↔ Commitment)
        for proj in projects:
            _add_edge_if_new("Project", proj.name, "Memory", entry_title, "documented_in", proj.confidence)
            for comm in commitments:
                _add_edge_if_new("Project", proj.name, "Commitment", comm.description[:80], "requires", comm.confidence)

        # 4. Place & Activity Relationships (Place ↔ Memory, Place ↔ Activity, Activity ↔ Place)
        for pl in places:
            _add_edge_if_new("Place", pl.name, "Memory", entry_title, "featured_in", pl.confidence)
            for ac in activities:
                _add_edge_if_new("Activity", ac.name, "Place", pl.name, "took_place_at", 0.92)
                _add_edge_if_new("Place", pl.name, "Activity", ac.name, "hosted", 0.92)

        # Commitments with project default fallback
        for comm in commitments:
            proj_name = comm.project or (projects[0].name if projects else "Personal Goals")
            _add_edge_if_new("Project", proj_name, "Commitment", comm.description[:80], "requires", comm.confidence)

        db.commit()


    # -----------------------------------------------------------------------
    # 5. FORGETTING & SMART LIFE INSIGHTS
    # -----------------------------------------------------------------------
    @staticmethod
    def get_smart_insights(user_id: str, db: Session) -> Dict[str, Any]:
        """
        Aggregates genuine user intelligence signals:
        - Unresolved commitments (pending, overdue, or due soon)
        - Upcoming important dates
        - Active routine deviations
        - Frequent collaborators and places
        - Real life observations (grounded strictly in user data)
        """
        now = datetime.now(timezone.utc)

        # 1. Commitments
        commitments = db.query(Commitment).filter(Commitment.user_id == user_id).all()
        pending_comms = [c for c in commitments if c.status == "PENDING"]
        completed_comms = [c for c in commitments if c.status == "COMPLETED"]

        # Urgent / Overdue / Upcoming commitments
        urgent_comms = []
        for c in pending_comms:
            days_ago = 0
            if c.created_at:
                c_dt = c.created_at if c.created_at.tzinfo else c.created_at.replace(tzinfo=timezone.utc)
                days_ago = max(0, (now - c_dt).days)

            urgent_comms.append({
                "id": c.id,
                "title": c.description,
                "project": c.project or "Personal",
                "due_date": c.due_date or "Upcoming",
                "priority": c.priority,
                "days_ago": days_ago,
                "is_stale": days_ago >= 3
            })

        # 2. Routine Deviations
        deviations = MemoryIntelligenceService.check_routine_deviations(user_id, db)
        deviation_alerts = [
            {
                "routine_id": r.id,
                "title": r.title,
                "activity": r.activity,
                "pattern": r.pattern,
                "prompt": r.deviation_prompt
            }
            for r in deviations
        ]

        # 3. Top Collaborators & Places
        entities = db.query(Entity).filter(Entity.user_id == user_id).all()
        people_counts: Dict[str, int] = defaultdict(int)
        places_counts: Dict[str, int] = defaultdict(int)
        for e in entities:
            if e.type == "person":
                people_counts[e.name] += 1
            elif e.type == "place":
                places_counts[e.name] += 1

        top_people = sorted([{"name": k, "count": v} for k, v in people_counts.items()], key=lambda x: x["count"], reverse=True)[:5]
        top_places = sorted([{"name": k, "count": v} for k, v in places_counts.items()], key=lambda x: x["count"], reverse=True)[:5]

        # 4. Total memories
        total_memories = db.query(DiaryEntry).filter(DiaryEntry.user_id == user_id).count()

        # 5. Formulate Grounded AI Observations (Zero hallucinations)
        observations: List[str] = []
        if deviation_alerts:
            observations.append(f"Habit notice: {deviation_alerts[0]['prompt']}")
        elif total_memories >= 2:
            observations.append("You maintain a consistent cadence across your logged activities.")

        if top_people:
            observations.append(f"Most frequent collaborator: {top_people[0]['name']} ({top_people[0]['count']} shared memories).")

        if top_places:
            observations.append(f"Top frequented location: {top_places[0]['name']} ({top_places[0]['count']} visits logged).")

        if len(pending_comms) > 0:
            observations.append(f"You have {len(pending_comms)} action items awaiting completion.")
        elif total_memories > 0:
            observations.append("All commitments are fulfilled. Great focus on execution!")

        return {
            "total_memories": total_memories,
            "commitments_summary": {
                "pending": len(pending_comms),
                "completed": len(completed_comms),
                "total": len(commitments),
                "urgent_items": urgent_comms
            },
            "routine_deviations": deviation_alerts,
            "top_people": top_people,
            "top_places": top_places,
            "ai_observations": observations
        }

    # -----------------------------------------------------------------------
    # 6. TODAY PROACTIVE LIFE ASSISTANT
    # -----------------------------------------------------------------------
    @staticmethod
    def get_today_assistant(user_id: str, db: Session) -> Dict[str, Any]:
        """
        Gathers real-time proactive assistant state for the authenticated user.
        Categorizes items by priority:
        - HIGH: Overdue commitments, deadlines today/soon, important unresolved commitments
        - MEDIUM: Upcoming commitments, routine deviations, stale items
        - LOW: Grounded life observations & habit insights
        Strictly user-isolated and non-hallucinatory.
        """
        from app.services.notification_service import notification_service
        from app.models.notification import Notification

        now = datetime.now(timezone.utc)
        
        # Sync reminder state
        notification_service.sync_reminders(user_id, db)
        
        # Check routine deviations
        deviations = MemoryIntelligenceService.check_routine_deviations(user_id, db)

        # 1. Fetch user's active commitments
        commitments = db.query(Commitment).filter(
            Commitment.user_id == user_id,
            Commitment.status.in_(["PENDING", "RESCHEDULED"])
        ).order_by(Commitment.created_at.desc()).all()

        needs_attention = []
        upcoming = []

        for c in commitments:
            due_dt = c.resolved_due_date
            if due_dt and due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)

            created_dt = c.created_at
            if created_dt and created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)

            days_ago = (now - created_dt).days if created_dt else 0

            if due_dt:
                diff_seconds = (due_dt - now).total_seconds()
                if diff_seconds < 0:
                    # Overdue
                    needs_attention.append({
                        "id": c.id,
                        "title": c.description,
                        "description": f"Overdue since {due_dt.strftime('%B %d')}. Project: {c.project or 'Personal'}",
                        "priority": "HIGH",
                        "category": "overdue",
                        "due_date": c.due_date or due_dt.strftime("%B %d"),
                        "resolved_due_date": due_dt.isoformat(),
                        "source_entry_id": c.diary_entry_id,
                        "days_ago": days_ago,
                        "action_label": "Mark Done",
                        "extra_data": {"project": c.project}
                    })
                elif diff_seconds <= 86400 * 2:
                    # Due today or tomorrow
                    needs_attention.append({
                        "id": c.id,
                        "title": c.description,
                        "description": f"Due soon ({c.due_date or due_dt.strftime('%B %d')}). Project: {c.project or 'Personal'}",
                        "priority": "HIGH",
                        "category": "due_soon",
                        "due_date": c.due_date or "Today/Soon",
                        "resolved_due_date": due_dt.isoformat(),
                        "source_entry_id": c.diary_entry_id,
                        "days_ago": days_ago,
                        "action_label": "Mark Done",
                        "extra_data": {"project": c.project}
                    })
                else:
                    # Upcoming in future
                    upcoming.append({
                        "id": c.id,
                        "title": c.description,
                        "description": f"Scheduled for {c.due_date or due_dt.strftime('%B %d')}. Project: {c.project or 'Personal'}",
                        "priority": "MEDIUM",
                        "category": "upcoming",
                        "due_date": c.due_date or due_dt.strftime("%B %d"),
                        "resolved_due_date": due_dt.isoformat(),
                        "source_entry_id": c.diary_entry_id,
                        "days_ago": days_ago,
                        "action_label": "View Details",
                        "extra_data": {"project": c.project}
                    })
            else:
                if days_ago >= 3:
                    # Stale commitment
                    needs_attention.append({
                        "id": c.id,
                        "title": c.description,
                        "description": f"Unresolved task logged {days_ago} days ago. Project: {c.project or 'Personal'}",
                        "priority": "MEDIUM",
                        "category": "stale",
                        "due_date": c.due_date or "Pending",
                        "resolved_due_date": None,
                        "source_entry_id": c.diary_entry_id,
                        "days_ago": days_ago,
                        "action_label": "Resolve",
                        "extra_data": {"project": c.project}
                    })
                else:
                    upcoming.append({
                        "id": c.id,
                        "title": c.description,
                        "description": f"Pending task: {c.description}",
                        "priority": "MEDIUM",
                        "category": "upcoming",
                        "due_date": c.due_date or "Upcoming",
                        "resolved_due_date": None,
                        "source_entry_id": c.diary_entry_id,
                        "days_ago": days_ago,
                        "action_label": "View",
                        "extra_data": {"project": c.project}
                    })

        # 2. Routine changes
        routine_changes = []
        for r in deviations:
            routine_changes.append({
                "id": r.id,
                "title": f"Habit Change: {r.title}",
                "description": r.deviation_prompt or f"Deviation noticed in {r.title}",
                "priority": "MEDIUM",
                "category": "routine_deviation",
                "due_date": r.pattern,
                "resolved_due_date": None,
                "source_entry_id": None,
                "days_ago": None,
                "action_label": "Review Routine",
                "extra_data": {"routine_id": r.id, "activity": r.activity, "pattern": r.pattern}
            })

        # 3. Active notifications / reminders
        notifs = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).order_by(Notification.created_at.desc()).limit(10).all()

        reminders = [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "category": n.category,
                "channel": n.channel,
                "created_at": n.created_at.isoformat() if n.created_at else None,
                "metadata": n.metadata_json or {}
            }
            for n in notifs
        ]

        # 4. Smart life observations
        smart_insights = MemoryIntelligenceService.get_smart_insights(user_id, db)
        observations = smart_insights.get("ai_observations", [])

        # Check empty state
        is_empty = (
            len(needs_attention) == 0 and
            len(upcoming) == 0 and
            len(routine_changes) == 0 and
            len(reminders) == 0 and
            len(observations) == 0
        )

        return {
            "date": now.strftime("%A, %B %d, %Y"),
            "greeting": "Here is your proactive briefing for today:" if not is_empty else "You are all caught up for today!",
            "needs_attention": needs_attention,
            "upcoming": upcoming,
            "routine_changes": routine_changes,
            "reminders": reminders,
            "insights": observations,
            "is_empty": is_empty
        }


memory_intelligence_service = MemoryIntelligenceService()
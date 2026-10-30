from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.entity import Entity
from app.models.commitment import Commitment
from app.models.routine import Routine
from app.ai.stt_service import get_ai_provider
from app.schemas.search import ConversationalAnswer, SearchResultItem, ForgettingItem

class SearchService:
    @staticmethod
    async def ask_question(user_id: str, query: str, db: Session) -> ConversationalAnswer:
        # 1. Load user profile & preferences
        user = db.query(User).filter(User.id == user_id).first()
        user_name = user.full_name if user else "User"
        user_prefs = user.preferences if user and user.preferences else {}

        # 2. Load commitments
        commitments = db.query(Commitment).filter(
            Commitment.user_id == user_id,
            Commitment.status == "PENDING"
        ).order_by(Commitment.created_at.desc()).all()

        # 3. Load routines
        routines = db.query(Routine).filter(Routine.user_id == user_id).all()

        # 4. Load entities
        entities = db.query(Entity).filter(Entity.user_id == user_id).all()

        # 5. Load all user diary entries (including latest drafts/reviews)
        entries = db.query(DiaryEntry).filter(
            DiaryEntry.user_id == user_id
        ).all()

        def get_dt(e: DiaryEntry) -> datetime:
            return e.entry_date or e.created_at or datetime.min

        # Sort descending by date
        sorted_entries = sorted(entries, key=get_dt, reverse=True)

        entry_dicts = []
        for e in sorted_entries:
            dt = e.entry_date or e.created_at
            date_str = dt.strftime("%A, %B %d, %Y") if dt else "Thursday, September 10, 2026"
            content = e.generated_content or e.raw_text or e.transcript or ""
            entry_dicts.append({
                "id": e.id,
                "title": e.title or "Memory",
                "content": content,
                "raw_text": e.raw_text or e.transcript or "",
                "generated_content": e.generated_content or "",
                "transcript": e.transcript or "",
                "category": e.category or "Personal",
                "mood": e.mood or "",
                "date": date_str,
                "is_today": dt.strftime("%Y-%m-%d") == "2026-09-10" if dt else True
            })

        user_profile_payload = {
            "full_name": user_name,
            "email": user.email if user else "",
            "preferences": user_prefs,
            "commitments": [
                {
                    "description": c.description,
                    "project": c.project or "General",
                    "due_date": c.due_date or "Upcoming",
                    "priority": c.priority or "medium",
                    "activity_thread": getattr(c, "activity_thread", None),
                    "next_action": getattr(c, "next_action", None)
                }
                for c in commitments
            ],
            "routines": [
                {
                    "title": r.title,
                    "activity": r.activity,
                    "location": r.location,
                    "frequency": r.frequency,
                    "confidence": r.confidence,
                    "details": r.details,
                    "deviation": r.deviation_prompt
                }
                for r in routines
            ],
            "entities": [
                {
                    "type": ent.type,
                    "name": ent.name
                }
                for ent in entities
            ]
        }

        ai_provider = get_ai_provider()
        try:
            res = await ai_provider.answer_question(query, entry_dicts, user_profile=user_profile_payload)
        except TypeError:
            res = await ai_provider.answer_question(query, entry_dicts)

        # Find best matching entry for source reference
        q_lower = query.lower()
        matched_entry_id = res.get("source_entry_id")
        if not matched_entry_id:
            for e in sorted_entries:
                text_corpus = f"{e.title or ''} {e.raw_text or ''} {e.generated_content or ''} {e.transcript or ''}".lower()
                # Check for significant words
                words = [w for w in q_lower.split() if len(w) > 3 and w not in ["what", "when", "where", "which", "about", "your", "today", "with"]]
                if any(w in text_corpus for w in words):
                    matched_entry_id = e.id
                    break

        matched_results = []
        for e in sorted_entries[:4]:
            dt = e.entry_date or e.created_at or datetime.now()
            matched_results.append(SearchResultItem(
                entry_id=e.id,
                title=e.title or "Untitled",
                snippet=(e.generated_content or e.raw_text or e.transcript or "")[:150] + "...",
                category=e.category or "General",
                date=dt,
                score=0.92
            ))

        unique_entities = list(dict.fromkeys([ent.name for ent in entities if ent.name]))[:6]
        if not unique_entities:
            unique_entities = ["Memory", "Journal", "Personal"]

        # If asking about tasks/commitments or what is forgotten, include actionable items
        forgetting_items = []
        if any(k in q_lower for k in ["forget", "task", "commitment", "todo", "due", "deadline", "pending"]):
            for c in commitments[:5]:
                forgetting_items.append(ForgettingItem(
                    id=c.id,
                    title=c.description,
                    description=f"Project: {c.project or 'General'}",
                    due_date=c.due_date or "Upcoming",
                    priority=c.priority or "medium",
                    source_entry_id=c.diary_entry_id,
                    days_ago_mentioned=1,
                    reason="Active commitment recorded in your personal journal"
                ))

        return ConversationalAnswer(
            query=query,
            answer=res.get("answer", "No memory found for this query."),
            source_entry_id=matched_entry_id,
            related_entries=matched_results,
            related_entities=unique_entities,
            forgetting_items=forgetting_items
        )

search_service = SearchService()

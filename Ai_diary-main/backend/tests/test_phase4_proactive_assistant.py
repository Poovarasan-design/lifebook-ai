"""
Phase 4 Tests: Proactive Life Assistant
Tests cover:
  1. Upcoming reminder creation
  2. Overdue reminder creation (HIGH priority)
  3. Completed commitment excluded from generating reminders
  4. Duplicate reminder prevention
  5. Routine deviation proactive insight
  6. Forgetting insight generation
  7. Empty Today state
  8. Strict user isolation for all proactive features
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.commitment import Commitment
from app.models.routine import Routine
from app.models.notification import Notification
from app.services.notification_service import notification_service
from app.services.memory_intelligence_service import memory_intelligence_service
from app.services.commitment_service import commitment_service
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _get_or_create_user(email: str, name: str, db):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        from app.core.security import get_password_hash
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            full_name=name,
            hashed_password=get_password_hash("Pass1234!"),
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def test_upcoming_reminder():
    db = SessionLocal()
    try:
        user = _get_or_create_user("user_p4_upcoming@lifebook.ai", "P4 User", db)
        now = datetime.now(timezone.utc)
        due_future = now + timedelta(days=4)

        c = Commitment(
            id=str(uuid.uuid4()),
            user_id=user.id,
            description="Submit Phase 4 Milestone Report",
            project="AI Assistant Project",
            due_date=due_future.strftime("%B %d"),
            resolved_due_date=due_future,
            status="PENDING",
            priority="medium"
        )
        db.add(c)
        db.commit()

        notifs = notification_service.sync_reminders(user.id, db)
        assert len(notifs) >= 1
        notif = [n for n in notifs if n.metadata_json.get("commitment_id") == c.id][0]
        assert notif.metadata_json.get("reminder_stage") == "upcoming"
        assert notif.metadata_json.get("priority") == "medium"
        assert "Submit Phase 4" in notif.title
    finally:
        db.close()


def test_overdue_reminder():
    db = SessionLocal()
    try:
        user = _get_or_create_user("user_p4_overdue@lifebook.ai", "P4 Overdue User", db)
        now = datetime.now(timezone.utc)
        past_due = now - timedelta(days=2)

        c = Commitment(
            id=str(uuid.uuid4()),
            user_id=user.id,
            description="Renew Cloud Hosting Subscription",
            project="Infrastructure",
            due_date="2 days ago",
            resolved_due_date=past_due,
            status="PENDING",
            priority="high"
        )
        db.add(c)
        db.commit()

        notifs = notification_service.sync_reminders(user.id, db)
        assert len(notifs) >= 1
        overdue_notif = [n for n in notifs if n.metadata_json.get("commitment_id") == c.id][0]
        assert overdue_notif.metadata_json.get("reminder_stage") == "overdue"
        assert overdue_notif.metadata_json.get("priority") == "high"
        assert "Overdue" in overdue_notif.title
    finally:
        db.close()


def test_completed_commitment_excluded():
    db = SessionLocal()
    try:
        user = _get_or_create_user("user_p4_completed@lifebook.ai", "P4 Completed User", db)
        now = datetime.now(timezone.utc)
        due_dt = now - timedelta(days=1)

        c = Commitment(
            id=str(uuid.uuid4()),
            user_id=user.id,
            description="Completed Presentation Task",
            project="Presentation",
            due_date="Yesterday",
            resolved_due_date=due_dt,
            status="COMPLETED",
            priority="high"
        )
        db.add(c)
        db.commit()

        notifs = notification_service.sync_reminders(user.id, db)
        matching = [n for n in notifs if n.metadata_json.get("commitment_id") == c.id]
        assert len(matching) == 0, "Completed commitments must never generate reminders"
    finally:
        db.close()


def test_duplicate_reminder_prevention():
    db = SessionLocal()
    try:
        user = _get_or_create_user("user_p4_dedup@lifebook.ai", "P4 Dedup User", db)
        now = datetime.now(timezone.utc)
        due_dt = now + timedelta(days=3)

        c = Commitment(
            id=str(uuid.uuid4()),
            user_id=user.id,
            description="Prepare Hackathon Deck",
            project="Hackathon",
            due_date=due_dt.strftime("%B %d"),
            resolved_due_date=due_dt,
            status="PENDING",
            priority="medium"
        )
        db.add(c)
        db.commit()

        # First sync
        first_sync = notification_service.sync_reminders(user.id, db)
        assert any(n.metadata_json.get("commitment_id") == c.id for n in first_sync)

        # Second sync immediately
        second_sync = notification_service.sync_reminders(user.id, db)
        matching_second = [n for n in second_sync if n.metadata_json.get("commitment_id") == c.id]
        assert len(matching_second) == 0, "Second sync must not generate duplicate reminder"
    finally:
        db.close()


def test_routine_deviation_insight():
    db = SessionLocal()
    try:
        user = _get_or_create_user("user_p4_dev@lifebook.ai", "P4 Dev User", db)
        
        # Add a Friday workout routine observed 3 times
        r = Routine(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title="Friday Workout",
            activity="Workout & Fitness at Gym",
            pattern="Friday",
            frequency="weekly",
            occurrence_count=3,
            confidence=0.88,
            is_active=True,
            deviation_active=False
        )
        db.add(r)
        
        # Add a Friday diary entry that did not mention gym/workout
        friday_date = datetime(2026, 10, 2, 12, 0, 0, tzinfo=timezone.utc) # 2026-10-02 is Friday
        entry = DiaryEntry(
            id=str(uuid.uuid4()),
            user_id=user.id,
            input_type="text",
            title="Friday Movie Night",
            raw_text="Stayed home and watched a documentary movie all evening with popcorn.",
            category="Leisure",
            status="CONFIRMED",
            entry_date=friday_date
        )
        db.add(entry)
        db.commit()

        # Check deviations
        deviations = memory_intelligence_service.check_routine_deviations(user.id, db)
        assert len(deviations) >= 1
        assert any(d.title == "Friday Workout" and d.deviation_active for d in deviations)

        # Check Today Assistant surfaces this routine change
        today_data = memory_intelligence_service.get_today_assistant(user.id, db)
        assert len(today_data["routine_changes"]) >= 1
        assert any("Workout" in item["title"] for item in today_data["routine_changes"])
    finally:
        db.close()


def test_forgetting_insight():
    db = SessionLocal()
    try:
        user = _get_or_create_user("user_p4_forget@lifebook.ai", "P4 Forget User", db)
        now = datetime.now(timezone.utc)
        
        # Add an unresolved commitment from 4 days ago
        created_dt = now - timedelta(days=4)
        c = Commitment(
            id=str(uuid.uuid4()),
            user_id=user.id,
            description="Follow up with Dr. Nathan on research paper",
            project="Research",
            due_date="Earlier this week",
            status="PENDING",
            priority="high",
            created_at=created_dt
        )
        db.add(c)
        db.commit()

        forgetting = commitment_service.get_forgetting_commitments(user.id, db)
        assert len(forgetting.items) >= 1
        item = [it for it in forgetting.items if it.id == c.id][0]
        assert item.days_ago_mentioned >= 3
        assert "research" in item.description.lower() or "follow up" in item.title.lower()
    finally:
        db.close()


def test_empty_today_state():
    db = SessionLocal()
    try:
        user = _get_or_create_user("user_p4_empty@lifebook.ai", "P4 Empty User", db)
        # Clear any data for this user
        db.query(Commitment).filter(Commitment.user_id == user.id).delete()
        db.query(Routine).filter(Routine.user_id == user.id).delete()
        db.query(DiaryEntry).filter(DiaryEntry.user_id == user.id).delete()
        db.query(Notification).filter(Notification.user_id == user.id).delete()
        db.commit()

        today_data = memory_intelligence_service.get_today_assistant(user.id, db)
        assert today_data["is_empty"] is True
        assert len(today_data["needs_attention"]) == 0
        assert len(today_data["upcoming"]) == 0
        assert len(today_data["routine_changes"]) == 0
        assert len(today_data["reminders"]) == 0
        assert "all caught up" in today_data["greeting"].lower()
    finally:
        db.close()


def test_user_isolation_proactive_assistant():
    db = SessionLocal()
    try:
        user_a = _get_or_create_user("user_p4_a@lifebook.ai", "User A", db)
        user_b = _get_or_create_user("user_p4_b@lifebook.ai", "User B", db)

        # User A has overdue task
        now = datetime.now(timezone.utc)
        c_a = Commitment(
            id=str(uuid.uuid4()),
            user_id=user_a.id,
            description="User A Secret Task",
            project="Project A",
            due_date="Yesterday",
            resolved_due_date=now - timedelta(days=1),
            status="PENDING",
            priority="high"
        )
        db.add(c_a)
        db.commit()

        today_a = memory_intelligence_service.get_today_assistant(user_a.id, db)
        today_b = memory_intelligence_service.get_today_assistant(user_b.id, db)

        assert any(item["id"] == c_a.id for item in today_a["needs_attention"])
        assert not any(item["id"] == c_a.id for item in today_b["needs_attention"])
        assert not any("User A" in item.get("title", "") for item in today_b["needs_attention"])
        assert not any("User A" in item.get("title", "") for item in today_b["upcoming"])
    finally:
        db.close()

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.commitment import Commitment
from app.models.notification import Notification
from app.services.commitment_service import CommitmentService
from app.services.notification_service import notification_service
from app.core.security import get_password_hash

def test_temporal_commitment_parsing():
    base_dt = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc) # Monday, Oct 5, 2026

    # Test 1: Today 8:14pm I have a google meeting
    dt1, label1, is_past1 = CommitmentService.parse_temporal_due_date("Today 8:14pm I have a google meeting", base_dt)
    tasks1 = CommitmentService.extract_tasks_from_text("Today 8:14pm I have a google meeting")
    assert "Google Meeting" in tasks1
    assert "Today" in label1
    assert "8:14 PM" in label1
    assert dt1.hour == 20
    assert dt1.minute == 14

    # Test 2: Tomorrow at 10 AM I have an association function
    dt2, label2, is_past2 = CommitmentService.parse_temporal_due_date("Tomorrow at 10 AM I have an association function", base_dt)
    tasks2 = CommitmentService.extract_tasks_from_text("Tomorrow at 10 AM I have an association function")
    assert "Association Function" in tasks2
    assert "Tomorrow" in label2
    assert "10:00 AM" in label2
    assert dt2.hour == 10
    assert dt2.minute == 0
    assert dt2.date() == base_dt.date() + timedelta(days=1)

    # Test 3: Next Monday I need to submit the project
    dt3, label3, is_past3 = CommitmentService.parse_temporal_due_date("Next Monday I need to submit the project", base_dt)
    tasks3 = CommitmentService.extract_tasks_from_text("Next Monday I need to submit the project")
    assert any("submit the project" in t.lower() for t in tasks3)
    assert "Next Monday" in label3
    assert dt3.date() == base_dt.date() + timedelta(days=7)

def test_past_date_statements_do_not_create_active_reminders():
    db = SessionLocal()
    try:
        user = User(
            email=f"past_{uuid.uuid4().hex[:8]}@test.com",
            hashed_password=get_password_hash("TestPass123!"),
            full_name="Past Event User"
        )
        db.add(user)
        db.commit()

        entry = DiaryEntry(
            user_id=user.id,
            title="Yesterday's Lunch",
            raw_text="Yesterday at 3pm I met John for lunch",
            entry_date=datetime.now(timezone.utc) - timedelta(days=1),
            input_type="text",
            status="COMPLETED"
        )
        db.add(entry)
        db.commit()

        commitments = CommitmentService.extract_and_save_commitments(entry, db)
        # Past statements with no action/promise should not create pending commitments
        assert len(commitments) == 0
    finally:
        db.close()

def test_duplicate_memory_processing_prevents_duplicate_commitments():
    db = SessionLocal()
    try:
        user = User(
            email=f"dedup_{uuid.uuid4().hex[:8]}@test.com",
            hashed_password=get_password_hash("TestPass123!"),
            full_name="Dedup User"
        )
        db.add(user)
        db.commit()

        entry = DiaryEntry(
            user_id=user.id,
            title="Google Meeting Memory",
            raw_text="Today 8:14pm I have a google meeting",
            input_type="text",
            status="SAVED"
        )
        db.add(entry)
        db.commit()

        # Process first time
        comms1 = CommitmentService.extract_and_save_commitments(entry, db)
        assert len(comms1) == 1
        assert "Google Meeting" in comms1[0].description

        # Re-process same entry (e.g. user re-confirms or re-indexes)
        comms2 = CommitmentService.extract_and_save_commitments(entry, db)
        assert len(comms2) == 1

        total_in_db = db.query(Commitment).filter(Commitment.user_id == user.id).count()
        assert total_in_db == 1
    finally:
        db.close()

def test_user_isolation_for_commitments():
    db = SessionLocal()
    try:
        user_a = User(email=f"user_a_{uuid.uuid4().hex[:8]}@test.com", hashed_password=get_password_hash("Pass123!"), full_name="User A")
        user_b = User(email=f"user_b_{uuid.uuid4().hex[:8]}@test.com", hashed_password=get_password_hash("Pass123!"), full_name="User B")
        db.add_all([user_a, user_b])
        db.commit()

        entry_a = DiaryEntry(
            user_id=user_a.id,
            title="User A Meeting",
            raw_text="Today 8:14pm I have a google meeting",
            input_type="text",
            status="SAVED"
        )
        entry_b = DiaryEntry(
            user_id=user_b.id,
            title="User B Presentation",
            raw_text="Tomorrow at 10 AM I have an association function",
            input_type="text",
            status="SAVED"
        )
        db.add_all([entry_a, entry_b])
        db.commit()

        CommitmentService.extract_and_save_commitments(entry_a, db)
        CommitmentService.extract_and_save_commitments(entry_b, db)

        comms_a = CommitmentService.get_user_commitments(user_a.id, status=None, db=db)
        comms_b = CommitmentService.get_user_commitments(user_b.id, status=None, db=db)

        assert len(comms_a) == 1
        assert "Google Meeting" in comms_a[0].description
        assert len(comms_b) == 1
        assert "Association Function" in comms_b[0].description

        # Cross-check isolation
        assert all(c.user_id == user_a.id for c in comms_a)
        assert all(c.user_id == user_b.id for c in comms_b)
    finally:
        db.close()

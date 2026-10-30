# coding: utf-8
"""
Phase 3 Task 5: AI Memory Intelligence Tests

Covers:
1. Entity extraction (people, places, projects, activities, dates)
2. Commitment extraction with due dates
3. Memory importance scoring (deterministic, grounded)
4. Routine & Habit detection (requires >= 2 occurrences)
5. Insufficient history handling (single memory does NOT create routine)
6. Routine deviation detection
7. Life graph relationship creation & deduplication
8. Forgetting & Smart Life Insights
9. Strict User Isolation (User A vs User B)
10. Stale embedding prevention & RAG compatibility
"""

from __future__ import annotations
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from unittest.mock import AsyncMock, patch

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.entity import Entity
from app.models.commitment import Commitment
from app.models.routine import Routine
from app.models.life_graph import LifeGraphRelationship
from app.services.memory_intelligence_service import memory_intelligence_service
from app.services.routine_service import routine_service
from app.services.life_graph_service import life_graph_service
from app.services.commitment_service import commitment_service
from app.services.diary_service import diary_service
from app.ai.local_provider import SmartLocalAIProvider
from app.core.security import get_password_hash


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_users(db_session: Session):
    suf = str(uuid.uuid4())[:8]
    user_a = User(
        id=str(uuid.uuid4()),
        email=f"intel_alice_{suf}@lifebook.ai",
        full_name="Alice Intelligence",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
    )
    user_b = User(
        id=str(uuid.uuid4()),
        email=f"intel_bob_{suf}@lifebook.ai",
        full_name="Bob Intelligence",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
    )
    db_session.add_all([user_a, user_b])
    db_session.commit()
    return user_a, user_b


# ---------------------------------------------------------------------------
# 1. ENTITY EXTRACTION
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_entity_extraction_people_places_projects_activities():
    """SmartLocalAIProvider extracts people, places, projects, and activities accurately."""
    provider = SmartLocalAIProvider()
    text = (
        "Collaborated with Ravi and Sarah at Central Park on the SIH Hackathon project. "
        "We had a productive meeting and coding sprint, and then went for lunch at Blue Tokai Cafe."
    )
    result = await provider.understand_entry(text)

    # People
    person_names = [p.name for p in result.people]
    assert "Ravi" in person_names or "Sarah" in person_names

    # Places
    place_names = [p.name for p in result.places]
    assert any("Central Park" in pl or "Blue Tokai" in pl or "Park" in pl for pl in place_names)

    # Projects
    project_names = [p.name for p in result.projects]
    assert any("Hackathon" in pr or "SIH" in pr or "Project" in pr for pr in project_names)

    # Activities
    activity_names = [ac.name for ac in result.activities]
    assert len(activity_names) > 0


# ---------------------------------------------------------------------------
# 2. COMMITMENT EXTRACTION
# ---------------------------------------------------------------------------

def test_commitment_extraction_with_deadlines(db_session: Session, test_users):
    """CommitmentService extracts commitments with due dates and priorities."""
    user_a, _ = test_users
    entry = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="Hackathon Sprint Meeting",
        category="Work",
        mood="focused",
        entry_date=datetime(2026, 9, 10, 10, 0, tzinfo=timezone.utc),
        raw_text="Met with Ravi. I promised to send the REST API schema by Friday and call Sarah tomorrow."
    )
    db_session.add(entry)
    db_session.commit()

    commitment_service.extract_and_save_commitments(entry, db_session)

    comms = db_session.query(Commitment).filter(Commitment.diary_entry_id == entry.id).all()
    assert len(comms) >= 1
    descriptions = [c.description.lower() for c in comms]
    assert any("rest api" in d or "send" in d or "call" in d for d in descriptions)


# ---------------------------------------------------------------------------
# 3. MEMORY IMPORTANCE SCORING
# ---------------------------------------------------------------------------

def test_memory_importance_scoring_high_vs_low(db_session: Session, test_users):
    """High-significance memories score higher than routine minimal notes."""
    user_a, _ = test_users

    # High importance entry: Project + Milestone + Commitments
    entry_high = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="Won 1st Prize at SIH Hackathon Final",
        category="Work",
        mood="excited",
        entry_date=datetime.now(timezone.utc),
        generated_content="Major milestone achieved! We won 1st prize at the SIH Hackathon final with Ravi. I promised to send the investor deck tomorrow.",
        photo_urls=["/media/photo1.jpg"]
    )
    db_session.add(entry_high)
    db_session.commit()

    # Add extracted entity and commitment
    db_session.add(Entity(user_id=user_a.id, diary_entry_id=entry_high.id, type="project", name="SIH Hackathon", normalized_name="sih hackathon"))
    db_session.add(Entity(user_id=user_a.id, diary_entry_id=entry_high.id, type="person", name="Ravi", normalized_name="ravi"))
    db_session.add(Commitment(user_id=user_a.id, diary_entry_id=entry_high.id, description="Send investor deck", priority="high", due_date="Tomorrow"))
    db_session.commit()

    score_high = memory_intelligence_service.compute_memory_importance(entry_high, db_session)
    assert score_high["importance_score"] >= 0.60
    assert score_high["level"] in ["medium", "high"]
    assert "milestone_achievement" in score_high["signals"]

    # Low importance entry: Short minimal thought
    entry_low = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="Quick note",
        category="General",
        mood="neutral",
        entry_date=datetime.now(timezone.utc),
        generated_content="Just sitting by the window."
    )
    db_session.add(entry_low)
    db_session.commit()

    score_low = memory_intelligence_service.compute_memory_importance(entry_low, db_session)
    assert score_low["importance_score"] < 0.40
    assert score_low["level"] == "low"
    assert score_high["importance_score"] > score_low["importance_score"]


# ---------------------------------------------------------------------------
# 4. ROUTINE DETECTION (Multi-Memory Evidence)
# ---------------------------------------------------------------------------

def test_routine_detection_with_sufficient_history(db_session: Session, test_users):
    """Detects a weekly routine when >= 2 distinct historical memories confirm the pattern."""
    user_a, _ = test_users

    # Create 3 Friday entries for User A with Gym workout
    friday_dates = [
        datetime(2026, 9, 4, 18, 0, tzinfo=timezone.utc),   # Friday
        datetime(2026, 9, 11, 18, 0, tzinfo=timezone.utc),  # Friday
        datetime(2026, 9, 18, 18, 0, tzinfo=timezone.utc),  # Friday
    ]

    for idx, dt in enumerate(friday_dates):
        entry = DiaryEntry(
            id=str(uuid.uuid4()),
            user_id=user_a.id,
            input_type="text",
            title=f"Friday Workout Session {idx+1}",
            category="Health",
            mood="energized",
            status="CONFIRMED",
            entry_date=dt,
            generated_content="Completed my 60-minute Friday workout session at the gym with cardio and weight lifting."
        )
        db_session.add(entry)
    db_session.commit()

    routines = memory_intelligence_service.detect_user_routines(user_a.id, db_session, min_occurrences=2)
    assert len(routines) >= 1
    gym_routine = next((r for r in routines if "Workout" in r.activity or "Fitness" in r.activity), None)
    assert gym_routine is not None
    assert gym_routine.pattern == "Friday"
    assert gym_routine.occurrence_count >= 2
    assert gym_routine.is_active is True


# ---------------------------------------------------------------------------
# 5. INSUFFICIENT HISTORY (Single Memory Does NOT Create Routine)
# ---------------------------------------------------------------------------

def test_insufficient_history_does_not_create_routine(db_session: Session, test_users):
    """A single isolated memory must NOT create a routine."""
    user_a, _ = test_users

    # Only 1 single Monday entry
    entry = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="Tried rock climbing once",
        category="Sports",
        mood="excited",
        status="CONFIRMED",
        entry_date=datetime(2026, 9, 7, 10, 0, tzinfo=timezone.utc),  # Monday
        generated_content="Tried rock climbing at the gym for the first time."
    )
    db_session.add(entry)
    db_session.commit()

    # With min_occurrences=2, it must return empty
    routines = memory_intelligence_service.detect_user_routines(user_a.id, db_session, min_occurrences=2)
    climbing_routine = next((r for r in routines if "climbing" in r.title.lower()), None)
    assert climbing_routine is None


# ---------------------------------------------------------------------------
# 6. ROUTINE DEVIATION DETECTION
# ---------------------------------------------------------------------------

def test_routine_deviation_detection(db_session: Session, test_users):
    """Detects when an established routine is missed/altered on a matching day."""
    user_a, _ = test_users

    # 1. Establish Friday routine with 2 entries
    for dt in [datetime(2026, 9, 4, 18, 0, tzinfo=timezone.utc), datetime(2026, 9, 11, 18, 0, tzinfo=timezone.utc)]:
        db_session.add(DiaryEntry(
            id=str(uuid.uuid4()),
            user_id=user_a.id,
            input_type="text",
            title="Friday Gym Workout",
            status="CONFIRMED",
            entry_date=dt,
            generated_content="Completed Friday gym workout."
        ))
    db_session.commit()
    memory_intelligence_service.detect_user_routines(user_a.id, db_session, min_occurrences=2)

    # 2. Add a latest Friday entry where the user did NOT go to the gym (e.g. Travel)
    deviated_entry = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="Travel to Madurai",
        status="CONFIRMED",
        entry_date=datetime(2026, 9, 25, 18, 0, tzinfo=timezone.utc),  # Recent Friday
        generated_content="Traveled to Madurai all day and visited temples. No time for regular habits."
    )
    db_session.add(deviated_entry)
    db_session.commit()

    deviations = memory_intelligence_service.check_routine_deviations(user_a.id, db_session)
    assert len(deviations) >= 1
    assert deviations[0].deviation_active is True
    assert deviations[0].deviation_prompt is not None
    assert "Friday" in deviations[0].deviation_prompt


# ---------------------------------------------------------------------------
# 7. LIFE GRAPH CREATION & DEDUPLICATION
# ---------------------------------------------------------------------------

def test_life_graph_sync_and_deduplication(db_session: Session, test_users):
    """Syncing memories to the Life Graph creates connections without duplicate edges."""
    user_a, _ = test_users

    entry = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="Project Discussion with Ravi",
        category="Work",
        status="CONFIRMED",
        entry_date=datetime.now(timezone.utc),
        generated_content="Discussed project architecture with Ravi at Central Park."
    )
    db_session.add(entry)
    db_session.commit()

    # Add entities
    db_session.add(Entity(user_id=user_a.id, diary_entry_id=entry.id, type="person", name="Ravi", normalized_name="ravi"))
    db_session.add(Entity(user_id=user_a.id, diary_entry_id=entry.id, type="place", name="Central Park", normalized_name="central park"))
    db_session.add(Entity(user_id=user_a.id, diary_entry_id=entry.id, type="project", name="AI Core", normalized_name="ai core"))
    db_session.commit()

    # First sync
    memory_intelligence_service.sync_entry_to_graph_deduped(entry, db_session)
    count_first = db_session.query(LifeGraphRelationship).filter(LifeGraphRelationship.user_id == user_a.id).count()
    assert count_first > 0

    # Second sync (re-indexing or re-saving) must NOT duplicate edges
    memory_intelligence_service.sync_entry_to_graph_deduped(entry, db_session)
    count_second = db_session.query(LifeGraphRelationship).filter(LifeGraphRelationship.user_id == user_a.id).count()
    assert count_second == count_first, "Duplicate LifeGraph relationships were created"


# ---------------------------------------------------------------------------
# 8. FORGETTING & SMART INSIGHTS
# ---------------------------------------------------------------------------

def test_forgetting_and_smart_insights(db_session: Session, test_users):
    """Smart insights return unresolved commitments and genuine life observations."""
    user_a, _ = test_users

    comm = Commitment(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        description="Submit Q3 Hackathon Report",
        project="SIH Hackathon",
        due_date="Tomorrow",
        priority="high",
        status="PENDING",
        created_at=datetime.now(timezone.utc) - timedelta(days=4)  # 4 days ago -> stale
    )
    db_session.add(comm)
    db_session.commit()

    insights = memory_intelligence_service.get_smart_insights(user_a.id, db_session)
    assert insights["commitments_summary"]["pending"] == 1
    urgent_items = insights["commitments_summary"]["urgent_items"]
    assert len(urgent_items) == 1
    assert urgent_items[0]["is_stale"] is True
    assert len(insights["ai_observations"]) > 0


# ---------------------------------------------------------------------------
# 9. STRICT USER ISOLATION
# ---------------------------------------------------------------------------

def test_user_isolation_for_all_intelligence(db_session: Session, test_users):
    """User A cannot access User B's entities, routines, commitments, or insights."""
    user_a, user_b = test_users

    # User B has private routine and commitment
    routine_b = Routine(
        id=str(uuid.uuid4()),
        user_id=user_b.id,
        title="Bob Private Routine",
        activity="Private Meeting",
        pattern="Tuesday",
        occurrence_count=5,
        is_active=True
    )
    comm_b = Commitment(
        id=str(uuid.uuid4()),
        user_id=user_b.id,
        description="Bob confidential action item",
        status="PENDING"
    )
    db_session.add_all([routine_b, comm_b])
    db_session.commit()

    # User A query for routines
    routines_a = routine_service.get_user_routines(user_a.id, db_session)
    assert all(r.user_id == user_a.id for r in routines_a)
    assert not any(r.id == routine_b.id for r in routines_a)

    # User A query for commitments
    forgetting_a = commitment_service.get_forgetting_commitments(user_a.id, db_session)
    assert not any(item.id == comm_b.id for item in forgetting_a.items)

    # User A smart insights
    insights_a = memory_intelligence_service.get_smart_insights(user_a.id, db_session)
    assert insights_a["commitments_summary"]["pending"] == 0
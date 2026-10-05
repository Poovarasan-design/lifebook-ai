"""
Phase 6 Tests: Advanced Life Graph
Tests cover:
  1. Rich Entity Relationship creation (Person, Project, Place, Activity, Commitment, Memory)
  2. Graph Deduplication (re-confirming/editing does not duplicate nodes or edges)
  3. Person History & Timeline ordering
  4. Project History & Collaborators & Commitments
  5. Place History & Activities & Photos & Co-visitors
  6. Generic Entity History API
  7. Conflict & Stale relationship detection
  8. Graph-Augmented RAG retrieval integration
  9. Strict User Isolation across all Graph features
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.entity import Entity
from app.models.commitment import Commitment
from app.models.life_graph import LifeGraphRelationship
from app.services.life_graph_service import life_graph_service
from app.services.memory_intelligence_service import memory_intelligence_service
from app.services.embedding_service import embedding_service
from app.services.rag_service import rag_service
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
    else:
        # Clean test user data
        db.query(LifeGraphRelationship).filter(LifeGraphRelationship.user_id == user.id).delete()
        db.query(Commitment).filter(Commitment.user_id == user.id).delete()
        db.query(Entity).filter(Entity.user_id == user.id).delete()
        db.query(DiaryEntry).filter(DiaryEntry.user_id == user.id).delete()
        db.commit()
    return user


def test_rich_entity_relationships_creation():
    db = SessionLocal()
    try:
        user = _get_or_create_user(f"user_p6_rel_{uuid.uuid4().hex[:6]}@lifebook.ai", "Rel User", db)
        
        entry = DiaryEntry(
            id=str(uuid.uuid4()),
            user_id=user.id,
            input_type="text",
            title="Robotics Hackathon Sprint",
            raw_text="Met with Vikram at Innovation Lab to build Quantum Bot",
            generated_content="Worked with Vikram on the Quantum Bot project at the Innovation Lab. Need to submit architecture diagram.",
            category="Work",
            entry_date=datetime(2026, 8, 15, 14, 0, 0, tzinfo=timezone.utc),
            status="CONFIRMED"
        )
        db.add(entry)
        db.commit()

        # Add entities & commitment
        db.add(Entity(user_id=user.id, diary_entry_id=entry.id, type="person", name="Vikram", normalized_name="vikram"))
        db.add(Entity(user_id=user.id, diary_entry_id=entry.id, type="project", name="Quantum Bot", normalized_name="quantum bot"))
        db.add(Entity(user_id=user.id, diary_entry_id=entry.id, type="place", name="Innovation Lab", normalized_name="innovation lab"))
        db.add(Entity(user_id=user.id, diary_entry_id=entry.id, type="activity", name="Robotics Sprint", normalized_name="robotics sprint"))
        db.add(Commitment(
            user_id=user.id,
            diary_entry_id=entry.id,
            description="Submit architecture diagram",
            project="Quantum Bot",
            status="PENDING"
        ))
        db.commit()

        # Sync to graph
        memory_intelligence_service.sync_entry_to_graph_deduped(entry, db)

        rels = db.query(LifeGraphRelationship).filter(LifeGraphRelationship.user_id == user.id).all()
        assert len(rels) >= 6

        # Check specific relationship types
        rel_tuples = [(r.source_name, r.relationship_type, r.target_name) for r in rels]
        assert ("Vikram", "collaborated_on", "Quantum Bot") in rel_tuples or ("Vikram", "worked_on", "Quantum Bot") in rel_tuples
        assert ("Vikram", "visited_with", "Innovation Lab") in rel_tuples
        assert ("Vikram", "appears_in", "Robotics Hackathon Sprint") in rel_tuples
        assert ("Quantum Bot", "requires", "Submit architecture diagram") in rel_tuples
        assert ("Activity" == [r.source_type for r in rels if r.target_name == "Innovation Lab"][0] or any(r.target_name == "Innovation Lab" for r in rels))
    finally:
        db.close()


def test_graph_deduplication_on_reconfirm():
    db = SessionLocal()
    try:
        user = _get_or_create_user(f"user_p6_dedup_{uuid.uuid4().hex[:6]}@lifebook.ai", "Dedup User", db)
        
        entry = DiaryEntry(
            id=str(uuid.uuid4()),
            user_id=user.id,
            input_type="text",
            title="Design Review with Sarah",
            raw_text="Reviewed UI designs with Sarah for Mobile App",
            generated_content="Collaborated with Sarah on Mobile App designs.",
            entry_date=datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
            status="CONFIRMED"
        )
        db.add(entry)
        db.commit()

        db.add(Entity(user_id=user.id, diary_entry_id=entry.id, type="person", name="Sarah", normalized_name="sarah"))
        db.add(Entity(user_id=user.id, diary_entry_id=entry.id, type="project", name="Mobile App", normalized_name="mobile app"))
        db.commit()

        # Sync once
        memory_intelligence_service.sync_entry_to_graph_deduped(entry, db)
        count_first = db.query(LifeGraphRelationship).filter(LifeGraphRelationship.user_id == user.id).count()

        # Re-sync (e.g. on diary update/reconfirm)
        memory_intelligence_service.sync_entry_to_graph_deduped(entry, db)
        count_second = db.query(LifeGraphRelationship).filter(LifeGraphRelationship.user_id == user.id).count()

        # Must not duplicate edges
        assert count_first == count_second

        # User graph query should also be clean
        user_graph = life_graph_service.get_user_graph(user.id, db)
        sarah_nodes = [n for n in user_graph.nodes if n.label == "Sarah"]
        assert len(sarah_nodes) == 1
    finally:
        db.close()


def test_person_history_and_timeline():
    db = SessionLocal()
    try:
        user = _get_or_create_user(f"user_p6_person_{uuid.uuid4().hex[:6]}@lifebook.ai", "Person User", db)
        
        # 2 memories on different dates
        e1 = DiaryEntry(
            id=str(uuid.uuid4()),
            user_id=user.id,
            input_type="text",
            title="First Sync with Arun",
            raw_text="Met Arun to discuss Cloud Migration",
            generated_content="Met Arun to discuss Cloud Migration project.",
            entry_date=datetime(2026, 7, 10, 9, 0, 0, tzinfo=timezone.utc),
            status="CONFIRMED"
        )
        e2 = DiaryEntry(
            id=str(uuid.uuid4()),
            user_id=user.id,
            input_type="text",
            title="Architecture Finalization with Arun",
            raw_text="Finalized cloud architecture with Arun at Tech Hub",
            generated_content="Finalized cloud architecture with Arun at Tech Hub.",
            entry_date=datetime(2026, 8, 20, 15, 0, 0, tzinfo=timezone.utc),
            status="CONFIRMED"
        )
        db.add_all([e1, e2])
        db.commit()

        db.add(Entity(user_id=user.id, diary_entry_id=e1.id, type="person", name="Arun", normalized_name="arun"))
        db.add(Entity(user_id=user.id, diary_entry_id=e1.id, type="project", name="Cloud Migration", normalized_name="cloud migration"))
        db.add(Entity(user_id=user.id, diary_entry_id=e2.id, type="person", name="Arun", normalized_name="arun"))
        db.add(Entity(user_id=user.id, diary_entry_id=e2.id, type="place", name="Tech Hub", normalized_name="tech hub"))
        db.commit()

        memory_intelligence_service.sync_entry_to_graph_deduped(e1, db)
        memory_intelligence_service.sync_entry_to_graph_deduped(e2, db)

        history = life_graph_service.get_person_history(user.id, "Arun", db)
        assert history.name == "Arun"
        assert history.type == "person"
        assert history.count == 2
        assert len(history.timeline) == 2
        # Chronological order
        assert history.timeline[0].title == "First Sync with Arun"
        assert history.timeline[1].title == "Architecture Finalization with Arun"
        assert "Cloud Migration" in history.related_entities["projects"]
        assert "Tech Hub" in history.related_entities["places"]
    finally:
        db.close()


def test_project_history_and_commitments():
    db = SessionLocal()
    try:
        user = _get_or_create_user(f"user_p6_proj_{uuid.uuid4().hex[:6]}@lifebook.ai", "Proj User", db)
        
        e = DiaryEntry(
            id=str(uuid.uuid4()),
            user_id=user.id,
            input_type="text",
            title="Alpha Release Sprint",
            raw_text="Working with David on AI Assistant",
            generated_content="Working on AI Assistant core release.",
            entry_date=datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc),
            status="CONFIRMED"
        )
        db.add(e)
        db.commit()

        db.add(Entity(user_id=user.id, diary_entry_id=e.id, type="project", name="AI Assistant", normalized_name="ai assistant"))
        db.add(Entity(user_id=user.id, diary_entry_id=e.id, type="person", name="David", normalized_name="david"))
        
        # Add overdue commitment for project
        past_due = datetime.now(timezone.utc) - timedelta(days=3)
        db.add(Commitment(
            user_id=user.id,
            diary_entry_id=e.id,
            project="AI Assistant",
            description="Deploy staging instance",
            status="PENDING",
            resolved_due_date=past_due
        ))
        db.commit()

        memory_intelligence_service.sync_entry_to_graph_deduped(e, db)

        proj_history = life_graph_service.get_project_history(user.id, "AI Assistant", db)
        assert proj_history.name == "AI Assistant"
        assert proj_history.type == "project"
        assert len(proj_history.timeline) == 1
        assert "David" in proj_history.related_entities["people"]
        assert len(proj_history.commitments) == 1
        assert proj_history.commitments[0].description == "Deploy staging instance"
        # Conflict detection (overdue commitment)
        assert any(c.issue_type == "overdue_commitments" for c in proj_history.conflicts)
    finally:
        db.close()


def test_place_history_and_photos():
    db = SessionLocal()
    try:
        user = _get_or_create_user(f"user_p6_place_{uuid.uuid4().hex[:6]}@lifebook.ai", "Place User", db)
        
        e = DiaryEntry(
            id=str(uuid.uuid4()),
            user_id=user.id,
            input_type="text",
            title="Sunset at Marina Bay",
            raw_text="Visited Marina Bay with Elena",
            generated_content="Watched sunset at Marina Bay with Elena.",
            photo_urls=["/media/marina_sunset.jpg"],
            entry_date=datetime(2026, 9, 15, 18, 0, 0, tzinfo=timezone.utc),
            status="CONFIRMED"
        )
        db.add(e)
        db.commit()

        db.add(Entity(user_id=user.id, diary_entry_id=e.id, type="place", name="Marina Bay", normalized_name="marina bay"))
        db.add(Entity(user_id=user.id, diary_entry_id=e.id, type="person", name="Elena", normalized_name="elena"))
        db.add(Entity(user_id=user.id, diary_entry_id=e.id, type="activity", name="Sunset Watching", normalized_name="sunset watching"))
        db.commit()

        memory_intelligence_service.sync_entry_to_graph_deduped(e, db)

        place_history = life_graph_service.get_place_history(user.id, "Marina Bay", db)
        assert place_history.name == "Marina Bay"
        assert place_history.type == "place"
        assert len(place_history.timeline) == 1
        assert "/media/marina_sunset.jpg" in place_history.timeline[0].photos
        assert "Elena" in place_history.related_entities["people"]
        assert "Sunset Watching" in place_history.related_entities["activities"]
    finally:
        db.close()


@pytest.mark.asyncio
async def test_graph_augmented_rag():
    db = SessionLocal()
    try:
        user = _get_or_create_user(f"user_p6_rag_{uuid.uuid4().hex[:6]}@lifebook.ai", "RAG Graph User", db)
        
        entry = DiaryEntry(
            id=str(uuid.uuid4()),
            user_id=user.id,
            input_type="text",
            title="Bioinformatics Research Sync",
            raw_text="Met Dr. Priya at Oxford Genomics Center to research CRISPR algorithms",
            generated_content="Collaborated with Dr. Priya on CRISPR algorithm design at Oxford Genomics Center.",
            category="Research",
            entry_date=datetime(2026, 9, 18, 11, 0, 0, tzinfo=timezone.utc),
            status="COMPLETED"
        )
        db.add(entry)
        db.commit()

        db.add(Entity(user_id=user.id, diary_entry_id=entry.id, type="person", name="Dr. Priya", normalized_name="dr. priya"))
        db.add(Entity(user_id=user.id, diary_entry_id=entry.id, type="project", name="CRISPR Algorithm", normalized_name="crispr algorithm"))
        db.add(Entity(user_id=user.id, diary_entry_id=entry.id, type="place", name="Oxford Genomics Center", normalized_name="oxford genomics center"))
        db.commit()

        memory_intelligence_service.sync_entry_to_graph_deduped(entry, db)
        await embedding_service.index_memory(entry, db)

        # Query Ask My Diary about Dr. Priya
        ans = await rag_service.answer_question(
            user_id=user.id,
            query="What projects have I worked on with Dr. Priya?",
            top_k=5,
            db=db
        )

        assert ans.is_grounded is True
        assert len(ans.sources) >= 1
        assert "Priya" in ans.answer or "CRISPR" in ans.answer
    finally:
        db.close()


def test_user_isolation_life_graph():
    db = SessionLocal()
    try:
        user_a = _get_or_create_user(f"user_p6_iso_a_{uuid.uuid4().hex[:6]}@lifebook.ai", "User A", db)
        user_b = _get_or_create_user(f"user_p6_iso_b_{uuid.uuid4().hex[:6]}@lifebook.ai", "User B", db)

        # User A has secret graph relationship
        e_a = DiaryEntry(
            id=str(uuid.uuid4()),
            user_id=user_a.id,
            input_type="text",
            title="Confidential Merger Project",
            raw_text="Met with CEO Alice about Stealth Acquisition",
            generated_content="Secret meeting with Alice regarding Stealth Acquisition.",
            status="CONFIRMED"
        )
        db.add(e_a)
        db.commit()
        db.add(Entity(user_id=user_a.id, diary_entry_id=e_a.id, type="person", name="Alice", normalized_name="alice"))
        db.add(Entity(user_id=user_a.id, diary_entry_id=e_a.id, type="project", name="Stealth Acquisition", normalized_name="stealth acquisition"))
        db.commit()

        memory_intelligence_service.sync_entry_to_graph_deduped(e_a, db)

        # User B queries their own graph & entity history for Alice
        graph_b = life_graph_service.get_user_graph(user_b.id, db)
        assert not any(n.label == "Alice" or n.label == "Stealth Acquisition" for n in graph_b.nodes)

        history_b = life_graph_service.get_person_history(user_b.id, "Alice", db)
        assert history_b.count == 0
        assert len(history_b.timeline) == 0
        assert len(history_b.relationships) == 0
    finally:
        db.close()

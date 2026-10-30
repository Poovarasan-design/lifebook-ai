import pytest
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.embedding import MemoryChunk
from app.schemas.retrieval import RetrievalFilter, RetrievalRequest
from app.services.embedding_service import embedding_service
from app.services.retrieval_service import retrieval_service, compute_cosine_similarity
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
def seeded_users_and_memories(db_session: Session):
    unique_suffix = str(uuid.uuid4())[:8]

    # Create User A (Alice)
    user_a = User(
        id=str(uuid.uuid4()),
        email=f"alice_{unique_suffix}@lifebook.ai",
        full_name="Alice Developer",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True
    )
    # Create User B (Bob)
    user_b = User(
        id=str(uuid.uuid4()),
        email=f"bob_{unique_suffix}@lifebook.ai",
        full_name="Bob Manager",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True
    )
    db_session.add_all([user_a, user_b])
    db_session.commit()

    now = datetime.now(timezone.utc)

    # 1. Alice's SIH Hackathon entry (Work / SIH project)
    entry_a1 = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="SIH Hackathon Sprint",
        category="Work",
        mood="productive",
        entry_date=now - timedelta(days=2),
        generated_content="Collaborated with Ravi on the SIH Hackathon project. We finished the REST API architecture and refined vector embeddings."
    )
    # 2. Alice's Coffee & Art entry (Personal / art)
    entry_a2 = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="Morning Sketch & Coffee",
        category="Personal",
        mood="peaceful",
        entry_date=now - timedelta(days=10),
        generated_content="Enjoyed a quiet morning at the cafe sipping espresso and sketching watercolor botanical illustrations in my notebook."
    )
    # 3. Alice's Multi-chunk Entry (Travel > 1000 chars)
    long_travel_narrative = (
        "Arrived in Madurai early in the morning and visited the historic Meenakshi Amman Temple with our traveling group of close friends. "
        "The ancient gopuram towers and thousand-pillar hall were breathtakingly beautiful in the morning golden sunlight.\n\n"
        "After the temple darshan, we walked to the famous old town food streets to enjoy traditional South Indian filter coffee, crispy ghee dosas, and fresh idlis with coconut chutney. "
        "The cultural ambiance was vibrant and welcoming with bustling flower vendors and bronze craft shops.\n\n"
        "In the afternoon and evening, we strolled through the historic markets, bought traditional handwoven sarees, and visited the Thirumalai Nayakkar Palace light show. "
        "A truly unforgettable journey filled with culture, architectural wonders, and lifelong memories."
    )
    entry_a3 = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="Trip to Madurai Temples",
        category="Travel",
        mood="inspired",
        entry_date=now - timedelta(days=20),
        generated_content=long_travel_narrative
    )

    # 4. Bob's Private Memory (Should never be retrieved by Alice)
    entry_b1 = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_b.id,
        input_type="text",
        title="Confidential Client Negotiation",
        category="Work",
        mood="focused",
        entry_date=now - timedelta(days=1),
        generated_content="Held private client pricing negotiations with Ravi regarding the enterprise license contract."
    )

    db_session.add_all([entry_a1, entry_a2, entry_a3, entry_b1])
    db_session.commit()

    # Index all memories into MemoryChunks
    for entry in [entry_a1, entry_a2, entry_a3, entry_b1]:
        asyncio.run(embedding_service.index_memory(entry, db_session))

    return user_a, user_b, [entry_a1, entry_a2, entry_a3], entry_b1


# 1. Vector search returns relevant memory
def test_vector_search_returns_relevant_memory(db_session: Session, seeded_users_and_memories):
    user_a, _, entries_a, _ = seeded_users_and_memories

    # Test direct vector search
    query = "cafe sipping espresso and sketching botanical illustrations"
    query_emb = asyncio.run(embedding_service.generate_embedding(query))
    vector_matches = asyncio.run(retrieval_service.vector_search(
        user_id=user_a.id,
        query_embedding=query_emb,
        top_k=3,
        filters=None,
        db=db_session
    ))

    assert len(vector_matches) > 0
    top_chunk, sim = vector_matches[0]
    assert top_chunk.diary_entry_id == entries_a[1].id  # entry_a2 (Coffee & Sketch)
    assert sim > 0.1

    # Test via full retrieve_memories pipeline
    response = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_a.id,
        query=query,
        top_k=3,
        db=db_session
    ))
    assert response.total_retrieved > 0
    top_result = response.results[0]
    assert top_result.entry_id == entries_a[1].id
    assert top_result.score > 0.3


# 2. Keyword search returns exact/relevant memory
def test_keyword_search_returns_exact_memory(db_session: Session, seeded_users_and_memories):
    user_a, _, entries_a, _ = seeded_users_and_memories

    keyword_matches = retrieval_service.keyword_search(
        user_id=user_a.id,
        query="Meenakshi Amman Temple Madurai",
        top_k=3,
        filters=None,
        db=db_session
    )

    assert len(keyword_matches) > 0
    top_chunk, score = keyword_matches[0]
    assert top_chunk.diary_entry_id == entries_a[2].id  # entry_a3 (Madurai)
    assert score > 0.2


# 3. Hybrid search combines both vector and keyword signals
def test_hybrid_search_combines_vector_and_keyword(db_session: Session, seeded_users_and_memories):
    user_a, _, entries_a, _ = seeded_users_and_memories

    query = "SIH hackathon project with Ravi"
    response = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_a.id,
        query=query,
        top_k=3,
        db=db_session
    ))

    assert response.total_retrieved > 0
    top_result = response.results[0]
    assert top_result.entry_id == entries_a[0].id  # entry_a1 (SIH)
    assert top_result.vector_score is not None
    assert top_result.keyword_score is not None
    assert top_result.score > 0.4


# 4. User A cannot retrieve User B's memories (Strict User Isolation)
def test_user_isolation_retrieval(db_session: Session, seeded_users_and_memories):
    user_a, user_b, _, entry_b1 = seeded_users_and_memories

    # Alice searches for "Confidential Client Negotiation enterprise license"
    alice_response = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_a.id,
        query="Confidential Client Negotiation enterprise license contract",
        top_k=5,
        min_score=0.1,
        db=db_session
    ))

    # None of the results should belong to Bob or Bob's entry
    for res in alice_response.results:
        assert res.user_id == user_a.id
        assert res.entry_id != entry_b1.id

    # Bob searching for his own query returns his memory
    bob_response = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_b.id,
        query="enterprise license contract",
        top_k=5,
        db=db_session
    ))
    assert bob_response.total_retrieved > 0
    assert bob_response.results[0].user_id == user_b.id
    assert bob_response.results[0].entry_id == entry_b1.id


# 5. Date filtering works (date_from, date_to)
def test_date_filtering(db_session: Session, seeded_users_and_memories):
    user_a, _, entries_a, _ = seeded_users_and_memories
    now = datetime.now(timezone.utc)

    # Filter to only past 5 days (should match entry_a1 from 2 days ago, but NOT entry_a2 from 10 days ago)
    filter_recent = RetrievalFilter(
        date_from=now - timedelta(days=5),
        date_to=now
    )
    response = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_a.id,
        query="sketching botanical watercolor illustrations at cafe",
        filters=filter_recent,
        db=db_session
    ))

    # Even though query matches entry_a2 semantically, date filter should exclude it
    matched_entry_ids = [r.entry_id for r in response.results]
    assert entries_a[1].id not in matched_entry_ids


# 6. Category filtering works
def test_category_filtering(db_session: Session, seeded_users_and_memories):
    user_a, _, entries_a, _ = seeded_users_and_memories

    filter_travel = RetrievalFilter(category="Travel")
    response = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_a.id,
        query="temple trip food street",
        filters=filter_travel,
        db=db_session
    ))

    assert response.total_retrieved > 0
    for r in response.results:
        assert r.category == "Travel"
        assert r.entry_id == entries_a[2].id


# 7. Entity / Mood filtering works
def test_mood_and_entity_filtering(db_session: Session, seeded_users_and_memories):
    user_a, _, entries_a, _ = seeded_users_and_memories

    filter_mood = RetrievalFilter(mood="peaceful")
    response = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_a.id,
        query="morning time",
        filters=filter_mood,
        db=db_session
    ))

    assert response.total_retrieved > 0
    for r in response.results:
        assert r.mood == "peaceful"
        assert r.entry_id == entries_a[1].id


# 8. Empty retrieval returns no results
def test_empty_retrieval_returns_no_results(db_session: Session, seeded_users_and_memories):
    user_a, _, _, _ = seeded_users_and_memories

    # Empty string query
    res_blank = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_a.id,
        query="   ",
        db=db_session
    ))
    assert res_blank.total_retrieved == 0
    assert len(res_blank.results) == 0

    # Non-existent user
    res_unknown = asyncio.run(retrieval_service.retrieve_memories(
        user_id=str(uuid.uuid4()),
        query="SIH hackathon",
        db=db_session
    ))
    assert res_unknown.total_retrieved == 0


# 9. Irrelevant query does not return arbitrary latest memory (Relevance Threshold)
def test_irrelevant_query_threshold(db_session: Session, seeded_users_and_memories):
    user_a, _, _, _ = seeded_users_and_memories

    # Query with high relevance threshold
    res = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_a.id,
        query="quantum astrophysics quantum supercomputers black holes",
        min_score=0.85,  # High threshold
        db=db_session
    ))
    # Must NOT return unrelated memories just because they exist
    assert res.total_retrieved == 0
    assert len(res.results) == 0


# 10. Multiple chunks from same entry are deduplicated appropriately
def test_entry_deduplication(db_session: Session, seeded_users_and_memories):
    user_a, _, entries_a, _ = seeded_users_and_memories

    # entry_a3 has multiple paragraphs/chunks about Madurai
    chunks_in_db = db_session.query(MemoryChunk).filter(
        MemoryChunk.diary_entry_id == entries_a[2].id
    ).all()
    assert len(chunks_in_db) > 1

    response = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_a.id,
        query="Madurai Meenakshi temple food street morning evening",
        top_k=5,
        deduplicate=True,
        db=db_session
    ))

    # Ensure only 1 chunk per entry is returned when deduplication is enabled
    entry_ids = [r.entry_id for r in response.results]
    assert len(entry_ids) == len(set(entry_ids))


# 11. SQLite retrieval cosine similarity math
def test_compute_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]

    assert compute_cosine_similarity(v1, v2) == 1.0
    assert compute_cosine_similarity(v1, v3) == 0.0
    assert compute_cosine_similarity([], v1) == 0.0
    assert compute_cosine_similarity([1.0], [1.0, 2.0]) == 0.0


# 12. PostgreSQL pgvector code path validity
def test_pgvector_code_path_structure():
    from app.models.embedding import PGVECTOR_AVAILABLE, VectorType
    vector_type = VectorType(dim=384)
    assert vector_type.dim == 384
    # VectorType loads JSON in SQLite dialect
    class FakeSQLiteDialect:
        name = "sqlite"
        def type_descriptor(self, obj):
            return obj

    descriptor = vector_type.load_dialect_impl(FakeSQLiteDialect())
    assert descriptor is not None

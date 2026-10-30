# coding: utf-8
"""
Task 3 + Task 4 Hardening Regression Tests
"""

from __future__ import annotations
import asyncio
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.embedding import MemoryChunk
from app.schemas.retrieval import RetrievedChunk, RetrievalResponse
from app.schemas.rag import RAGAnswer
from app.services.rag_service import RAGService
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
def two_users(db_session: Session):
    suf = str(uuid.uuid4())[:8]
    user_a = User(id=str(uuid.uuid4()), email=f"alice_h_{suf}@lifebook.ai",
                  full_name="Alice Hardening", hashed_password=get_password_hash("Test1234!"), is_active=True)
    user_b = User(id=str(uuid.uuid4()), email=f"bob_h_{suf}@lifebook.ai",
                  full_name="Bob Hardening", hashed_password=get_password_hash("Test1234!"), is_active=True)
    db_session.add_all([user_a, user_b])
    db_session.commit()
    return user_a, user_b


def _make_entry(user_id, title, content, category="Work"):
    return DiaryEntry(id=str(uuid.uuid4()), user_id=user_id, input_type="text",
                      title=title, category=category, mood="focused",
                      entry_date=datetime.now(timezone.utc), generated_content=content)


def _make_chunk(chunk_id="c1", entry_id="e1", user_id="u1", title="Test Memory",
                text="I worked on the OR-Tools integration.", score=0.92):
    return RetrievedChunk(chunk_id=chunk_id, entry_id=entry_id, user_id=user_id,
                          chunk_index=0, chunk_text=text, score=score,
                          vector_score=0.90, keyword_score=0.50, entry_date="2026-09-15",
                          title=title, category="Work", mood="focused",
                          metadata={"entities": [], "entry_id": entry_id, "user_id": user_id})


# T3-1: RealAIProvider has answer_question_grounded
@pytest.mark.asyncio
async def test_t3_1_real_ai_provider_has_grounded_method():
    from app.ai.openai_provider import RealAIProvider
    provider = RealAIProvider()
    assert hasattr(provider, "answer_question_grounded")
    user_msg = '''<RETRIEVED_MEMORIES>
[Memory 1]
Entry ID: e1
Date: 2026-09-15
Title: Yoga Morning
Category: Health
Content:
Did 30 minutes of yoga at sunrise.
</RETRIEVED_MEMORIES>

My question: what exercise did I do?'''
    result = await provider.answer_question_grounded(system_msg="You are LifeBook AI.", user_msg=user_msg)
    assert result is not None
    assert "Yoga Morning" in result or "30 minutes" in result


# T3-2: OpenRouter has no hardcoded stale September 2026 dates
def test_t3_2_openrouter_no_hardcoded_stale_date():
    import inspect
    from app.ai.openrouter_provider import OpenRouterProvider
    src = inspect.getsource(OpenRouterProvider.answer_question)
    assert "September 10, 2026" not in src
    assert "September 09, 2026" not in src


# T3-3: RAGService passes JWT user_id to retrieval (not altered)
@pytest.mark.asyncio
async def test_t3_3_rag_passes_jwt_user_id():
    svc = RAGService()
    captured = {}

    async def capture_retrieve(user_id, query, **kwargs):
        captured["user_id"] = user_id
        return RetrievalResponse(query=query, total_retrieved=0, results=[])

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", capture_retrieve):
        await svc.answer_question(user_id="jwt_user_xyz", query="test query")

    assert captured.get("user_id") == "jwt_user_xyz"


# T3-4: No memory -> LLM must NOT be called
@pytest.mark.asyncio
async def test_t3_4_no_memory_llm_not_called():
    svc = RAGService()
    llm_calls = []

    async def empty_retrieve(user_id, query, **kwargs):
        return RetrievalResponse(query=query, total_retrieved=0, results=[])

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", empty_retrieve), \
         patch("app.services.rag_service.get_ai_provider") as mock_pf:
        provider = AsyncMock()
        provider.answer_question_grounded = AsyncMock(side_effect=lambda **kw: llm_calls.append(1) or "called")
        mock_pf.return_value = provider
        answer = await svc.answer_question(user_id="u1", query="what did I do?")

    assert answer.is_grounded is False
    assert len(llm_calls) == 0, "LLM was invoked despite no retrieved memories"


# T3-5: Fake LLM citations not in sources
@pytest.mark.asyncio
async def test_t3_5_fake_citations_not_in_sources():
    svc = RAGService()
    chunk = _make_chunk()

    async def mock_retrieve(user_id, query, **kwargs):
        return RetrievalResponse(query=query, total_retrieved=1, results=[chunk])

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", mock_retrieve), \
         patch("app.services.rag_service.get_ai_provider") as mock_pf:
        provider = AsyncMock()
        provider.answer_question_grounded = AsyncMock(return_value="Amazing [Memory 99] [Memory 100].")
        mock_pf.return_value = provider
        answer = await svc.answer_question(user_id="u1", query="fake citation test")

    labels = [s.citation for s in answer.sources]
    assert "[Memory 99]" not in labels
    assert "[Memory 100]" not in labels


# T4-1: Embedding failure preserves original DiaryEntry
def test_t4_1_embedding_failure_preserves_diary_entry(db_session, two_users):
    user_a, _ = two_users
    entry = _make_entry(user_a.id, "Critical Memory", "Content that must survive failures.")
    db_session.add(entry)
    db_session.commit()

    with patch.object(embedding_service, "generate_embeddings", side_effect=RuntimeError("Embedding unavailable")):
        success = asyncio.run(embedding_service.index_memory(entry, db_session))

    assert success is False
    saved = db_session.query(DiaryEntry).filter(DiaryEntry.id == entry.id).first()
    assert saved is not None
    assert "Content that must survive failures." in saved.generated_content


# T4-2: Re-index removes stale chunks
def test_t4_2_reindex_removes_stale_chunks(db_session, two_users):
    user_a, _ = two_users
    entry = _make_entry(user_a.id, "Draft Entry", "Initial content before editing.")
    db_session.add(entry)
    db_session.commit()

    asyncio.run(embedding_service.index_memory(entry, db_session))
    old_ids = {c.id for c in db_session.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry.id).all()}
    assert len(old_ids) >= 1

    entry.generated_content = "Completely new content after the edit."
    db_session.commit()
    asyncio.run(embedding_service.index_memory(entry, db_session))

    new_chunks = db_session.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry.id).all()
    new_ids = {c.id for c in new_chunks}

    assert old_ids.isdisjoint(new_ids), "Stale chunk IDs still present after re-index"
    assert any("new content" in c.chunk_text for c in new_chunks)


# T4-3: Delete entry removes chunks
def test_t4_3_delete_entry_removes_chunks(db_session, two_users):
    user_a, _ = two_users
    entry = _make_entry(user_a.id, "Temp Memory", "This will be deleted.")
    db_session.add(entry)
    db_session.commit()

    asyncio.run(embedding_service.index_memory(entry, db_session))
    entry_id = entry.id
    assert db_session.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry_id).count() > 0

    db_session.delete(entry)
    db_session.commit()

    remaining = db_session.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry_id).count()
    assert remaining == 0


# T4-4: User B chunks never returned to User A
def test_t4_4_user_b_chunks_not_returned_to_user_a(db_session, two_users):
    user_a, user_b = two_users

    entry_a = _make_entry(user_a.id, "Alice Vector Work", "Alice researched vector embeddings deeply.")
    entry_b = _make_entry(user_b.id, "Bob Secret Work", "Bob researched vector embeddings secretly.")
    db_session.add_all([entry_a, entry_b])
    db_session.commit()

    asyncio.run(embedding_service.index_memory(entry_a, db_session))
    asyncio.run(embedding_service.index_memory(entry_b, db_session))

    response = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_a.id, query="vector embeddings research",
        top_k=10, min_score=0.0, db=db_session))

    for result in response.results:
        assert result.user_id == user_a.id
        assert result.entry_id != entry_b.id


# T4-5: RAGService retrieval always called with requesting user_id only
@pytest.mark.asyncio
async def test_t4_5_rag_context_scoped_to_requesting_user():
    svc = RAGService()
    user_a_chunk = _make_chunk(chunk_id="ca", entry_id="ea", user_id="user_a", title="Alice Memory")
    passed_user_ids = []

    async def scoped_retrieve(user_id, query, **kwargs):
        passed_user_ids.append(user_id)
        if user_id == "user_a":
            return RetrievalResponse(query=query, total_retrieved=1, results=[user_a_chunk])
        return RetrievalResponse(query=query, total_retrieved=0, results=[])

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", scoped_retrieve), \
         patch("app.services.rag_service.get_ai_provider") as mock_pf:
        provider = AsyncMock()
        provider.answer_question_grounded = AsyncMock(return_value="Found. [Memory 1]")
        mock_pf.return_value = provider
        await svc.answer_question(user_id="user_a", query="test context scoping")

    assert all(uid == "user_a" for uid in passed_user_ids)


# T4-6: Deduplication - 1 chunk per entry
def test_t4_6_deduplication_one_chunk_per_entry(db_session, two_users):
    user_a, _ = two_users
    long_content = (
        "Section 1: Visited SIH Hackathon final with Ravi and demonstrated the system.\n\n"
        "Section 2: Judges were impressed by the vector search pipeline and the results.\n\n"
        "Section 3: Won second prize and celebrated with the whole amazing team that evening."
    )
    entry = _make_entry(user_a.id, "SIH Final Day", long_content)
    db_session.add(entry)
    db_session.commit()

    asyncio.run(embedding_service.index_memory(entry, db_session))

    response = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_a.id, query="SIH Hackathon judges vector search prize",
        top_k=10, deduplicate=True, min_score=0.0, db=db_session))

    entry_id_counts: dict = {}
    for r in response.results:
        entry_id_counts[r.entry_id] = entry_id_counts.get(r.entry_id, 0) + 1

    for eid, count in entry_id_counts.items():
        assert count == 1, f"Entry {eid} appeared {count} times with deduplicate=True"


# T4-7: High threshold blocks irrelevant results
def test_t4_7_high_threshold_blocks_irrelevant(db_session, two_users):
    user_a, _ = two_users
    entry = _make_entry(user_a.id, "Cooking Pasta", "Made pasta with tomato sauce and basil for dinner.")
    db_session.add(entry)
    db_session.commit()

    asyncio.run(embedding_service.index_memory(entry, db_session))

    response = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_a.id, query="quantum physics gravitational wave black hole",
        min_score=0.90, top_k=5, db=db_session))

    assert response.total_retrieved == 0


# T4-8: RRF produces scored results
def test_t4_8_rrf_produces_scored_results(db_session, two_users):
    user_a, _ = two_users
    entry = _make_entry(user_a.id, "Morning Yoga", "Did 45 minutes of yoga and meditation at sunrise.")
    db_session.add(entry)
    db_session.commit()

    asyncio.run(embedding_service.index_memory(entry, db_session))

    response = asyncio.run(retrieval_service.retrieve_memories(
        user_id=user_a.id, query="yoga meditation morning sunrise",
        top_k=3, min_score=0.0, db=db_session))

    assert response.total_retrieved > 0
    top = response.results[0]
    assert (top.vector_score is not None) or (top.keyword_score is not None)


# T4-9: Cosine similarity edge cases
def test_t4_9_cosine_similarity_edge_cases():
    assert compute_cosine_similarity([], [1.0, 2.0]) == 0.0
    assert compute_cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0]) == 0.0
    assert compute_cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0
    assert compute_cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert compute_cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    sim = compute_cosine_similarity([1.0, 1.0, 0.0], [1.0, 0.0, 0.0])
    assert 0.0 < sim < 1.0


# T4-10: Embedding failure on one entry does not corrupt other entries' chunks
def test_t4_10_embedding_failure_does_not_corrupt_other_entries(db_session, two_users):
    user_a, _ = two_users
    entry_a = _make_entry(user_a.id, "Safe Entry A", "This entry must always survive any failure.")
    entry_b = _make_entry(user_a.id, "Failing Entry B", "This entry will fail during embedding.")
    db_session.add_all([entry_a, entry_b])
    db_session.commit()

    asyncio.run(embedding_service.index_memory(entry_a, db_session))
    chunks_a_before = db_session.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry_a.id).count()
    assert chunks_a_before >= 1

    original = embedding_service.generate_embeddings
    calls = [0]

    async def fail_once(texts):
        calls[0] += 1
        if calls[0] == 1:
            raise RuntimeError("Simulated embedding failure")
        return await original(texts)

    with patch.object(embedding_service, "generate_embeddings", side_effect=fail_once):
        success_b = asyncio.run(embedding_service.index_memory(entry_b, db_session))

    assert success_b is False
    chunks_a_after = db_session.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry_a.id).count()
    assert chunks_a_after == chunks_a_before, "Entry A chunks were corrupted by Entry B failure"
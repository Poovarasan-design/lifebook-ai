"""
Task 3 Tests: RAG Service — Grounded Generation + Ask My Diary Integration

Tests cover:
  1. Grounded answer returned with sources
  2. Cross-user isolation (user B cannot see user A memories)
  3. Empty query returns safe message
  4. No-memory query returns is_grounded=False
  5. Retrieved_count equals number of returned chunks
  6. Citation validation: invalid [Memory N] stripped from response
  7. Backward-compat: source_entry_id present
  8. Backward-compat: related_entries mirrors sources
  9. Backward-compat: related_entities populated
 10. LLM failure triggers deterministic fallback (no exception)
 11. Retrieval failure returns safe error message
 12. Top-K limit respected in retrieval call
 13. OpenRouterProvider.answer_question_grounded returns None when no API key
 14. SmartLocalAIProvider.answer_question_grounded returns context-based answer
"""

from __future__ import annotations
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from app.schemas.retrieval import RetrievedChunk, RetrievalResponse
from app.schemas.rag import RAGAnswer, RAGSource
from app.services.rag_service import (
    RAGService,
    build_context_block,
    validate_citations,
    _build_fallback_answer,
)


# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------

def _make_chunk(
    chunk_id: str = "c1",
    entry_id: str = "e1",
    user_id: str = "u1",
    title: str = "Test Memory",
    text: str = "I worked on the OR-Tools integration yesterday.",
    score: float = 0.92,
    date: str = "2026-09-15",
    category: str = "Work",
    mood: str = "focused",
    entities: list | None = None,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        entry_id=entry_id,
        user_id=user_id,
        chunk_index=0,
        chunk_text=text,
        score=score,
        vector_score=0.90,
        keyword_score=0.50,
        entry_date=date,
        title=title,
        category=category,
        mood=mood,
        metadata={"entities": entities or [], "entry_id": entry_id, "user_id": user_id},
    )


def _make_retrieval_response(chunks: List[RetrievedChunk], query: str = "test") -> RetrievalResponse:
    return RetrievalResponse(
        query=query,
        total_retrieved=len(chunks),
        results=chunks,
    )


def run(coro):
    """Helper to run a coroutine synchronously in tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Unit tests: build_context_block
# ---------------------------------------------------------------------------

def test_build_context_block_contains_memory_labels():
    chunk = _make_chunk()
    ctx, citation_map = build_context_block([chunk])
    assert "[Memory 1]" in ctx
    assert chunk.chunk_text in ctx
    assert 1 in citation_map
    assert citation_map[1] is chunk


def test_build_context_block_multiple_chunks():
    chunks = [
        _make_chunk(chunk_id="c1", entry_id="e1", text="First memory text"),
        _make_chunk(chunk_id="c2", entry_id="e2", text="Second memory text"),
    ]
    ctx, citation_map = build_context_block(chunks)
    assert "[Memory 1]" in ctx
    assert "[Memory 2]" in ctx
    assert 2 in citation_map


# ---------------------------------------------------------------------------
# Unit tests: validate_citations
# ---------------------------------------------------------------------------

def test_validate_citations_returns_valid_indices():
    chunk = _make_chunk()
    _, citation_map = build_context_block([chunk])
    valid = validate_citations("I worked on it [Memory 1] yesterday.", citation_map)
    assert valid == [1]


def test_validate_citations_rejects_out_of_range():
    chunk = _make_chunk()
    _, citation_map = build_context_block([chunk])
    # citation_map only has key 1; [Memory 99] must be rejected
    valid = validate_citations("Invented fact [Memory 99].", citation_map)
    assert valid == []


def test_validate_citations_no_duplicates():
    chunk = _make_chunk()
    _, citation_map = build_context_block([chunk])
    valid = validate_citations("[Memory 1] and [Memory 1] again.", citation_map)
    assert valid == [1]  # deduplicated


# ---------------------------------------------------------------------------
# Unit tests: _build_fallback_answer
# ---------------------------------------------------------------------------

def test_fallback_answer_no_chunks_returns_no_memory_message():
    from app.services.rag_service import build_context_block
    _, citation_map = build_context_block([])
    result = _build_fallback_answer([], citation_map)
    assert "couldn" in result.lower() or "no" in result.lower()


def test_fallback_answer_includes_chunk_title():
    chunk = _make_chunk(title="Sprint Planning", text="We planned the sprint for Q4.")
    _, citation_map = build_context_block([chunk])
    result = _build_fallback_answer([chunk], citation_map)
    assert "Sprint Planning" in result


# ---------------------------------------------------------------------------
# RAGService integration tests (mocked retrieval + LLM)
# ---------------------------------------------------------------------------

def _mock_retrieval(chunks: List[RetrievedChunk], query: str = "test"):
    response = _make_retrieval_response(chunks, query)
    return AsyncMock(return_value=response)


@pytest.fixture
def svc():
    return RAGService()


# Test 1: Grounded answer is returned with sources
@pytest.mark.asyncio
async def test_grounded_answer_has_sources(svc):
    chunk = _make_chunk()
    mock_retrieve = _mock_retrieval([chunk], query="what did I work on?")
    llm_answer = "You worked on OR-Tools integration. [Memory 1]"

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", mock_retrieve), \
         patch("app.services.rag_service.get_ai_provider") as mock_provider:
        provider = AsyncMock()
        provider.answer_question_grounded = AsyncMock(return_value=llm_answer)
        mock_provider.return_value = provider

        answer = await svc.answer_question(
            user_id="u1", query="what did I work on?"
        )

    assert isinstance(answer, RAGAnswer)
    assert len(answer.sources) >= 1
    assert answer.sources[0].entry_id == "e1"
    assert answer.is_grounded is True


# Test 2: Cross-user isolation
@pytest.mark.asyncio
async def test_cross_user_isolation_user_id_passed_to_retrieval(svc):
    chunk_user_a = _make_chunk(entry_id="ea", user_id="user_a", title="User A secret memory")
    captured_user_ids: list = []

    async def capture_retrieve(user_id, query, **kwargs):
        captured_user_ids.append(user_id)
        if user_id == "user_b":
            return _make_retrieval_response([])
        return _make_retrieval_response([chunk_user_a])

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", capture_retrieve), \
         patch("app.services.rag_service.get_ai_provider") as mock_provider:
        provider = AsyncMock()
        provider.answer_question_grounded = AsyncMock(return_value="No memories found.")
        mock_provider.return_value = provider

        answer_b = await svc.answer_question(user_id="user_b", query="what did user A do?")

    assert "user_b" in captured_user_ids
    assert answer_b.is_grounded is False
    all_source_entry_ids = [s.entry_id for s in answer_b.sources]
    assert "ea" not in all_source_entry_ids


# Test 3: Empty query returns safe message without crashing
@pytest.mark.asyncio
async def test_empty_query_returns_safe_message(svc):
    answer = await svc.answer_question(user_id="u1", query="")
    assert isinstance(answer, RAGAnswer)
    assert answer.is_grounded is False
    assert answer.sources == []


# Test 4: No relevant memories — is_grounded=False, no LLM called
@pytest.mark.asyncio
async def test_no_memories_returns_ungrounded_response(svc):
    mock_retrieve = _mock_retrieval([])

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", mock_retrieve), \
         patch("app.services.rag_service.get_ai_provider") as mock_provider:
        provider = AsyncMock()
        provider.answer_question_grounded = AsyncMock(return_value="should not be called")
        mock_provider.return_value = provider

        answer = await svc.answer_question(user_id="u1", query="what is my life plan?")

    assert answer.is_grounded is False
    assert answer.sources == []
    provider.answer_question_grounded.assert_not_called()


# Test 5: retrieved_count reflects number of chunks from retrieval service
@pytest.mark.asyncio
async def test_retrieved_count_matches_chunk_count(svc):
    chunks = [
        _make_chunk(chunk_id=f"c{i}", entry_id=f"e{i}", title=f"Memory {i}")
        for i in range(3)
    ]
    mock_retrieve = _mock_retrieval(chunks, query="test")

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", mock_retrieve), \
         patch("app.services.rag_service.get_ai_provider") as mock_provider:
        provider = AsyncMock()
        provider.answer_question_grounded = AsyncMock(
            return_value="Found [Memory 1] [Memory 2] [Memory 3]"
        )
        mock_provider.return_value = provider

        answer = await svc.answer_question(user_id="u1", query="test")

    assert answer.retrieved_count == 3


# Test 6: Fabricated citation rejected
@pytest.mark.asyncio
async def test_fabricated_citation_rejected(svc):
    chunk = _make_chunk()
    mock_retrieve = _mock_retrieval([chunk])

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", mock_retrieve), \
         patch("app.services.rag_service.get_ai_provider") as mock_provider:
        provider = AsyncMock()
        provider.answer_question_grounded = AsyncMock(
            return_value="You did something amazing [Memory 99]."
        )
        mock_provider.return_value = provider

        answer = await svc.answer_question(user_id="u1", query="what did I do?")

    citation_labels = [s.citation for s in answer.sources]
    assert "[Memory 99]" not in citation_labels


# Test 7: Backward-compat — source_entry_id set from first source
@pytest.mark.asyncio
async def test_backward_compat_source_entry_id(svc):
    chunk = _make_chunk(entry_id="entry_abc")
    mock_retrieve = _mock_retrieval([chunk])

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", mock_retrieve), \
         patch("app.services.rag_service.get_ai_provider") as mock_provider:
        provider = AsyncMock()
        provider.answer_question_grounded = AsyncMock(return_value="You worked. [Memory 1]")
        mock_provider.return_value = provider

        answer = await svc.answer_question(user_id="u1", query="what did I do?")

    assert answer.source_entry_id == "entry_abc"


# Test 8: Backward-compat — related_entries populated from sources
@pytest.mark.asyncio
async def test_backward_compat_related_entries_populated(svc):
    chunks = [
        _make_chunk(chunk_id="c1", entry_id="e1", title="Entry One"),
        _make_chunk(chunk_id="c2", entry_id="e2", title="Entry Two"),
    ]
    mock_retrieve = _mock_retrieval(chunks)

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", mock_retrieve), \
         patch("app.services.rag_service.get_ai_provider") as mock_provider:
        provider = AsyncMock()
        provider.answer_question_grounded = AsyncMock(
            return_value="See [Memory 1] and [Memory 2]."
        )
        mock_provider.return_value = provider

        answer = await svc.answer_question(user_id="u1", query="show memories")

    assert len(answer.related_entries) >= 1
    entry_ids = [e["entry_id"] for e in answer.related_entries]
    assert "e1" in entry_ids or "e2" in entry_ids


# Test 9: Backward-compat — related_entities from chunk metadata
@pytest.mark.asyncio
async def test_backward_compat_related_entities_from_metadata(svc):
    chunk = _make_chunk(entities=["Alice", "ProjectX"])
    mock_retrieve = _mock_retrieval([chunk])

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", mock_retrieve), \
         patch("app.services.rag_service.get_ai_provider") as mock_provider:
        provider = AsyncMock()
        provider.answer_question_grounded = AsyncMock(return_value="[Memory 1]")
        mock_provider.return_value = provider

        answer = await svc.answer_question(user_id="u1", query="who did I meet?")

    assert "Alice" in answer.related_entities
    assert "ProjectX" in answer.related_entities


# Test 10: LLM failure triggers deterministic fallback — no exception raised
@pytest.mark.asyncio
async def test_llm_failure_triggers_deterministic_fallback(svc):
    chunk = _make_chunk(title="Important Memory", text="Very important content here.")
    mock_retrieve = _mock_retrieval([chunk])

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", mock_retrieve), \
         patch("app.services.rag_service.get_ai_provider") as mock_provider:
        provider = AsyncMock()
        provider.answer_question_grounded = AsyncMock(side_effect=Exception("API timeout"))
        mock_provider.return_value = provider

        answer = await svc.answer_question(user_id="u1", query="what is important?")

    assert isinstance(answer, RAGAnswer)
    assert "Important Memory" in answer.answer or answer.sources


# Test 11: Retrieval service failure returns safe error response
@pytest.mark.asyncio
async def test_retrieval_failure_returns_safe_error(svc):
    async def fail_retrieve(*args, **kwargs):
        raise RuntimeError("DB connection lost")

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", fail_retrieve):
        answer = await svc.answer_question(user_id="u1", query="what happened?")

    assert isinstance(answer, RAGAnswer)
    assert answer.is_grounded is False
    assert "error" in answer.answer.lower() or "try again" in answer.answer.lower()


# Test 12: Top-K limit is passed through to retrieval service
@pytest.mark.asyncio
async def test_top_k_passed_to_retrieval(svc):
    captured_kwargs: dict = {}

    async def capture_retrieve(user_id, query, top_k, **kwargs):
        captured_kwargs["top_k"] = top_k
        return _make_retrieval_response([])

    with patch("app.services.rag_service.retrieval_service.retrieve_memories", capture_retrieve):
        await svc.answer_question(user_id="u1", query="test", top_k=3)

    assert captured_kwargs["top_k"] == 3


# Test 13: OpenRouterProvider.answer_question_grounded returns None without API key
@pytest.mark.asyncio
async def test_openrouter_grounded_returns_none_without_api_key():
    from app.ai.openrouter_provider import OpenRouterProvider
    provider = OpenRouterProvider()
    with patch("app.ai.openrouter_provider.settings.OPENROUTER_API_KEY", None):
        result = await provider.answer_question_grounded(
            system_msg="You are helpful.",
            user_msg="What did I do?"
        )
        assert result is None


# Test 14: SmartLocalAIProvider.answer_question_grounded returns context-based answer
@pytest.mark.asyncio
async def test_local_provider_grounded_returns_context_based_answer():
    from app.ai.local_provider import SmartLocalAIProvider

    provider = SmartLocalAIProvider()
    user_msg = """<RETRIEVED_MEMORIES>
[Memory 1]
Entry ID: e1
Date: 2026-09-15
Title: Sprint Planning
Category: Work
Content:
We planned Q4 sprints.
</RETRIEVED_MEMORIES>

My question: what did I plan?"""

    result = await provider.answer_question_grounded(
        system_msg="You are LifeBook AI.",
        user_msg=user_msg,
    )

    assert result is not None
    assert "Sprint Planning" in result or "Q4" in result

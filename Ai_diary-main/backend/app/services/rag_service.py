"""
RAGService — Grounded Retrieval-Augmented Generation for Ask My Diary.

Architecture:
    1. Authenticate user_id (ALWAYS from JWT, never from request).
    2. Call RetrievalService (Task 2) to retrieve relevant MemoryChunks.
    3. If no relevant chunks: return safe no-memory response (no LLM call).
    4. Build a compact, token-budgeted grounded context string.
    5. Call the existing AI provider with a strict grounded prompt.
    6. Parse the LLM response and validate every citation against retrieved chunks.
    7. Remove/ignore invalid or fabricated citations.
    8. Return RAGAnswer with structured sources.

Anti-hallucination guarantees:
    - LLM is NEVER called when retrieval returns nothing.
    - Prompt instructs LLM to answer ONLY from supplied context.
    - Citation validator rejects any [Memory N] not in retrieved list.
    - SmartLocalAIProvider fallback also answers from context only.
"""

from __future__ import annotations
import re
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.rag import RAGSource, RAGAnswer
from app.schemas.retrieval import RetrievalFilter, RetrievedChunk
from app.services.retrieval_service import retrieval_service
from app.ai.stt_service import get_ai_provider

logger = logging.getLogger(__name__)

# Maximum characters of chunk text to include per memory in the LLM context.
_CHUNK_CONTEXT_LIMIT = 600
# Maximum total characters in the assembled context block sent to the LLM.
_TOTAL_CONTEXT_LIMIT = 6000
# Citation pattern — matches [Memory 1], [Memory 12], etc.
_CITATION_RE = re.compile(r"\[Memory\s+(\d+)\]", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Context Builder
# ---------------------------------------------------------------------------

def build_context_block(chunks: List[RetrievedChunk]) -> Tuple[str, Dict[int, RetrievedChunk]]:
    """
    Build a numbered, compact context string from retrieved chunks.

    Returns:
        context_text: Formatted block for the LLM system prompt.
        citation_map: Mapping of Memory N → RetrievedChunk for validation.
    """
    citation_map: Dict[int, RetrievedChunk] = {}
    parts: List[str] = []
    total_chars = 0

    for i, chunk in enumerate(chunks, start=1):
        citation_map[i] = chunk

        title = chunk.title or "Memory"
        date_str = chunk.entry_date or "Unknown date"
        category = chunk.category or "Personal"
        text = (chunk.chunk_text or "").strip()

        # Respect per-chunk character budget
        if len(text) > _CHUNK_CONTEXT_LIMIT:
            text = text[:_CHUNK_CONTEXT_LIMIT].rstrip() + "..."

        block = (
            f"[Memory {i}]\n"
            f"Entry ID: {chunk.entry_id}\n"
            f"Date: {date_str}\n"
            f"Title: {title}\n"
            f"Category: {category}\n"
            f"Content:\n{text}\n"
        )

        if total_chars + len(block) > _TOTAL_CONTEXT_LIMIT:
            logger.debug("Context budget reached at Memory %d/%d", i, len(chunks))
            break

        parts.append(block)
        total_chars += len(block)

    return "\n---\n".join(parts), citation_map


# ---------------------------------------------------------------------------
# Citation Validator
# ---------------------------------------------------------------------------

def validate_citations(
    answer: str,
    citation_map: Dict[int, RetrievedChunk],
) -> List[int]:
    """
    Extract all [Memory N] citations from the answer and validate them.

    Returns a list of valid memory indices (1-based).
    Invalid indices (not in citation_map) are silently ignored.
    """
    found = _CITATION_RE.findall(answer)
    valid: List[int] = []
    seen = set()
    for num_str in found:
        n = int(num_str)
        if n in citation_map and n not in seen:
            valid.append(n)
            seen.add(n)
    return valid


# ---------------------------------------------------------------------------
# Grounded Prompt Builder
# ---------------------------------------------------------------------------

def build_grounded_prompt(
    user_name: str,
    query: str,
    context_block: str,
    graph_context: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Build the system and user messages for the grounded RAG prompt.

    Strict rules instruct the LLM to answer ONLY from the supplied context.
    """
    today = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")

    system_msg = f"""You are LifeBook AI, the personal, trustworthy diary assistant for {user_name}.

STRICT GROUNDING RULES — YOU MUST FOLLOW THESE WITHOUT EXCEPTION:
1. Answer using ONLY the memory entries supplied in <RETRIEVED_MEMORIES> and verified relationships in <LIFE_GRAPH_CONNECTIONS> below.
2. Do NOT invent, assume, or fabricate any person, date, event, project, activity, or commitment.
3. Do NOT use the user's question itself as evidence of any fact.
4. If the retrieved memories do not contain the answer, say so honestly and clearly.
5. Do NOT treat absence of information as permission to guess.
6. Cite every memory you use with its label, e.g. "...discussed OR-Tools. [Memory 1]"
7. Only use citation labels that appear in <RETRIEVED_MEMORIES>. Never invent [Memory N] labels.
8. Keep answers natural, warm, and useful — formatted with bullet points for readability.
9. Today's date is: {today}.

ANTI-HALLUCINATION CONTRACT:
- If you cannot find the answer in the provided memories, respond with:
  "I couldn't find a relevant memory in your LifeBook for that question."
- Never reveal any information that is not in the retrieved memories below.
"""

    graph_section = f"\n<LIFE_GRAPH_CONNECTIONS>\n{graph_context}\n</LIFE_GRAPH_CONNECTIONS>\n" if graph_context else ""

    user_msg = f"""<RETRIEVED_MEMORIES>
{context_block}
</RETRIEVED_MEMORIES>
{graph_section}
My question: {query}

Please answer based only on the memories above, citing each one you use."""

    return system_msg, user_msg


# ---------------------------------------------------------------------------
# RAGService
# ---------------------------------------------------------------------------

class RAGService:
    """
    Grounded Retrieval-Augmented Generation service.

    Orchestrates: retrieval → context building → LLM call → citation validation.
    """

    async def answer_question(
        self,
        user_id: str,
        query: str,
        filters: Optional[RetrievalFilter] = None,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        db: Optional[Session] = None,
        user_name: str = "you",
    ) -> RAGAnswer:
        """
        Full grounded RAG pipeline for Ask My Diary.

        Args:
            user_id:   JWT-authenticated user ID. NEVER accept from frontend.
            query:     User's natural-language question.
            filters:   Optional RetrievalFilter (date, category, entities).
            top_k:     Max chunks to retrieve (defaults to RAG_TOP_K setting).
            min_score: Minimum relevance threshold (defaults to RAG_MIN_RELEVANCE_SCORE).
            db:        SQLAlchemy session. Opens its own if None.
            user_name: Display name for the grounded prompt.

        Returns:
            RAGAnswer with sources, is_grounded flag, and backward-compat fields.
        """
        if not user_id or not query or not query.strip():
            return RAGAnswer(
                query=query or "",
                answer="Please ask a question about your memories.",
                is_grounded=False,
            )

        k = top_k or settings.RAG_TOP_K
        threshold = min_score if min_score is not None else settings.RAG_MIN_RELEVANCE_SCORE

        # ------------------------------------------------------------------
        # STEP 1: Retrieve relevant memory chunks (Task 2 RetrievalService)
        # ------------------------------------------------------------------
        try:
            retrieval_response = await retrieval_service.retrieve_memories(
                user_id=user_id,
                query=query.strip(),
                top_k=k,
                filters=filters,
                min_score=threshold,
                deduplicate=True,
                db=db,
            )
        except Exception as exc:
            logger.error("RAG retrieval failed for user %s: %s", user_id, exc, exc_info=True)
            return RAGAnswer(
                query=query,
                answer="I encountered an error retrieving your memories. Please try again.",
                is_grounded=False,
            )

        retrieved_chunks = retrieval_response.results

        # ------------------------------------------------------------------
        # STEP 2: No-memory guard — do NOT call LLM if nothing was found
        # ------------------------------------------------------------------
        if not retrieved_chunks:
            logger.info(
                "RAG: no relevant memories for user %s query %r", user_id, query[:60]
            )
            return RAGAnswer(
                query=query,
                answer=(
                    "I couldn't find a relevant memory in your LifeBook for that question. "
                    "Try asking about something you have recorded in your diary."
                ),
                sources=[],
                retrieved_count=0,
                is_grounded=False,
            )

        # ------------------------------------------------------------------
        # STEP 3: Build grounded context block & fetch Life Graph context
        # ------------------------------------------------------------------
        context_block, citation_map = build_context_block(retrieved_chunks)

        graph_context = ""
        if db is not None:
            try:
                from app.services.life_graph_service import life_graph_service
                graph_context = life_graph_service.get_graph_context_for_rag(user_id, query.strip(), db)
            except Exception as e:
                logger.debug(f"Could not fetch graph context for RAG: {e}")

        # ------------------------------------------------------------------
        # STEP 4: Call LLM with strict grounded prompt
        # ------------------------------------------------------------------
        ai_provider = get_ai_provider()
        system_msg, user_msg = build_grounded_prompt(
            user_name=user_name,
            query=query.strip(),
            context_block=context_block,
            graph_context=graph_context,
        )


        raw_answer: Optional[str] = None
        try:
            if hasattr(ai_provider, "answer_question_grounded"):
                raw_answer = await ai_provider.answer_question_grounded(
                    system_msg=system_msg,
                    user_msg=user_msg,
                )
            else:
                # Fallback: use answer_question with context assembled as entry dicts
                entry_dicts = _chunks_to_entry_dicts(retrieved_chunks, citation_map)
                result = await ai_provider.answer_question(query.strip(), entry_dicts)
                raw_answer = result.get("answer", "")
        except Exception as exc:
            logger.error(
                "RAG LLM call failed for user %s: %s", user_id, exc, exc_info=True
            )
            # LLM failed but retrieval succeeded — return context-based answer
            raw_answer = _build_fallback_answer(retrieved_chunks, citation_map)

        if not raw_answer or not raw_answer.strip():
            raw_answer = _build_fallback_answer(retrieved_chunks, citation_map)

        # ------------------------------------------------------------------
        # STEP 5: Validate citations — reject any invented [Memory N] labels
        # ------------------------------------------------------------------
        valid_indices = validate_citations(raw_answer, citation_map)

        sources: List[RAGSource] = []
        for idx in valid_indices:
            chunk = citation_map[idx]
            sources.append(RAGSource(
                citation=f"[Memory {idx}]",
                entry_id=chunk.entry_id,
                chunk_id=chunk.chunk_id,
                title=chunk.title,
                date=chunk.entry_date,
                snippet=(chunk.chunk_text or "")[:200].strip() or None,
                score=round(chunk.score, 4),
                category=chunk.category,
                mood=chunk.mood,
            ))

        # If LLM cited nothing valid but we have context, include top source anyway
        if not sources and retrieved_chunks:
            top = retrieved_chunks[0]
            sources.append(RAGSource(
                citation="[Memory 1]",
                entry_id=top.entry_id,
                chunk_id=top.chunk_id,
                title=top.title,
                date=top.entry_date,
                snippet=(top.chunk_text or "")[:200].strip() or None,
                score=round(top.score, 4),
                category=top.category,
                mood=top.mood,
            ))

        # ------------------------------------------------------------------
        # STEP 6: Build backward-compatible legacy fields
        # ------------------------------------------------------------------
        primary_source_entry_id = sources[0].entry_id if sources else None

        related_entries = [
            {
                "entry_id": s.entry_id,
                "title": s.title or "Memory",
                "snippet": s.snippet or "",
                "category": s.category or "Personal",
                "date": s.date or "",
                "score": s.score,
                "matched_entities": [],
            }
            for s in sources
        ]

        # Unique entity names from all retrieved chunk metadata
        entity_names: List[str] = []
        seen_entities: set = set()
        for chunk in retrieved_chunks:
            for ent in (chunk.metadata or {}).get("entities", []):
                if ent and ent not in seen_entities:
                    entity_names.append(ent)
                    seen_entities.add(ent)

        return RAGAnswer(
            query=query.strip(),
            answer=raw_answer.strip(),
            sources=sources,
            retrieved_count=len(retrieved_chunks),
            is_grounded=True,
            source_entry_id=primary_source_entry_id,
            related_entries=related_entries,
            related_entities=entity_names[:8],
            forgetting_items=[],
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _chunks_to_entry_dicts(
    chunks: List[RetrievedChunk],
    citation_map: Dict[int, RetrievedChunk],
) -> List[Dict[str, Any]]:
    """Convert RetrievedChunks to entry dicts compatible with legacy answer_question."""
    seen_entries: set = set()
    result: List[Dict[str, Any]] = []
    for i, chunk in citation_map.items():
        if chunk.entry_id not in seen_entries:
            result.append({
                "id": chunk.entry_id,
                "title": chunk.title or f"Memory {i}",
                "content": chunk.chunk_text or "",
                "raw_text": chunk.chunk_text or "",
                "category": chunk.category or "Personal",
                "mood": chunk.mood or "",
                "date": chunk.entry_date or "",
            })
            seen_entries.add(chunk.entry_id)
    return result


def _build_fallback_answer(
    chunks: List[RetrievedChunk],
    citation_map: Dict[int, RetrievedChunk],
) -> str:
    """
    Build a deterministic grounded answer from retrieved chunks without LLM.
    Used when: API key missing, LLM timeout, or empty LLM response.
    NEVER fabricates facts — only uses retrieved context.
    """
    if not chunks:
        return "I couldn't find a relevant memory in your LifeBook for that question."

    lines = ["Here is what I found in your memories:\n"]
    for i, chunk in list(citation_map.items())[:3]:
        title = chunk.title or f"Memory {i}"
        date_str = chunk.entry_date or "Unknown date"
        snippet = (chunk.chunk_text or "")[:250].strip()
        lines.append(f"• {title} ({date_str}) [Memory {i}]\n  {snippet}")

    return "\n".join(lines)


# Singleton
rag_service = RAGService()

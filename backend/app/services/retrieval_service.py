import re
import math
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.core.config import settings
from app.models.embedding import MemoryChunk, PGVECTOR_AVAILABLE
from app.models.diary import DiaryEntry
from app.schemas.retrieval import RetrievalFilter, RetrievedChunk, RetrievalResponse
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd",
    "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that",
    "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's",
    "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom",
    "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
    "you're", "you've", "your", "yours", "yourself", "yourselves"
}


def compute_cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    Computes cosine similarity between two float vectors.
    Since embeddings from EmbeddingService are unit-normalized, dot product == cosine similarity.
    """
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 * norm2 < 1e-9:
        return 0.0
    similarity = dot / (norm1 * norm2)
    return max(0.0, min(1.0, float(similarity)))


class RetrievalService:
    """
    Hybrid Vector + Keyword Retrieval Service with RRF ranking,
    metadata filtering, deduplication, and strict user isolation.
    """

    # -------------------------------------------------------------------------
    # 1. METADATA FILTERING HELPER
    # -------------------------------------------------------------------------
    @staticmethod
    def _matches_metadata_filters(chunk: MemoryChunk, filters: Optional[RetrievalFilter]) -> bool:
        """
        Validates in-memory metadata filters against a chunk's metadata_info.
        """
        if not filters:
            return True

        meta = chunk.metadata_info or {}

        # Date range filters
        entry_date_raw = meta.get("entry_date")
        if entry_date_raw:
            try:
                if isinstance(entry_date_raw, str):
                    # Handle both ISO format and space-separated date strings
                    dt = datetime.fromisoformat(entry_date_raw.replace("Z", "+00:00"))
                elif isinstance(entry_date_raw, datetime):
                    dt = entry_date_raw
                else:
                    dt = None

                if dt:
                    # Strip timezone for naive comparison if needed
                    dt_naive = dt.replace(tzinfo=None)
                    if filters.date_from:
                        df_naive = filters.date_from.replace(tzinfo=None)
                        if dt_naive < df_naive:
                            return False
                    if filters.date_to:
                        dt_to_naive = filters.date_to.replace(tzinfo=None)
                        if dt_naive > dt_to_naive:
                            return False
            except Exception:
                pass

        # Category filter
        if filters.category:
            chunk_cat = str(meta.get("category", "")).lower()
            if filters.category.lower() not in chunk_cat:
                return False

        # Mood filter
        if filters.mood:
            chunk_mood = str(meta.get("mood", "")).lower()
            if filters.mood.lower() not in chunk_mood:
                return False

        # Entity filter
        if filters.entities:
            chunk_entities = [str(e).lower() for e in meta.get("entities", [])]
            requested = [str(e).lower() for e in filters.entities]
            # Must match at least one requested entity
            if not any(req in chunk_entities or any(req in ce for ce in chunk_entities) for req in requested):
                return False

        return True

    # -------------------------------------------------------------------------
    # 2. VECTOR RETRIEVAL
    # -------------------------------------------------------------------------
    async def vector_search(
        self,
        user_id: str,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[RetrievalFilter],
        db: Session
    ) -> List[Tuple[MemoryChunk, float]]:
        """
        Performs semantic vector search over MemoryChunk records.
        Strictly scoped by user_id.
        """
        if not user_id or not query_embedding:
            return []

        # Detect dialect safely — compatible with both SQLAlchemy 1.x and 2.x
        try:
            bind = db.get_bind()
            dialect_name = bind.dialect.name if bind else "sqlite"
        except Exception:
            try:
                dialect_name = db.bind.dialect.name if db.bind else "sqlite"
            except Exception:
                dialect_name = "sqlite"

        # 1. PostgreSQL with pgvector native search
        if dialect_name == "postgresql" and PGVECTOR_AVAILABLE:
            try:
                # Query distance using cosine distance
                query = db.query(
                    MemoryChunk,
                    (1.0 - MemoryChunk.embedding.cosine_distance(query_embedding)).label("similarity")
                ).filter(MemoryChunk.user_id == user_id)

                results = query.order_by(desc("similarity")).limit(top_k * 3).all()
                filtered = []
                for chunk, sim in results:
                    if self._matches_metadata_filters(chunk, filters):
                        filtered.append((chunk, float(sim)))
                    if len(filtered) >= top_k:
                        break
                return filtered
            except Exception as e:
                logger.warning(f"PostgreSQL pgvector query failed, falling back to Python scoring: {e}")

        # 2. SQLite / Local Python fallback
        chunks = db.query(MemoryChunk).filter(MemoryChunk.user_id == user_id).all()
        scored_chunks: List[Tuple[MemoryChunk, float]] = []

        for chunk in chunks:
            if not self._matches_metadata_filters(chunk, filters):
                continue
            emb = chunk.embedding
            if not emb:
                continue
            sim = compute_cosine_similarity(query_embedding, emb)
            scored_chunks.append((chunk, sim))

        # Sort descending by similarity
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    # -------------------------------------------------------------------------
    # 3. KEYWORD RETRIEVAL
    # -------------------------------------------------------------------------
    def keyword_search(
        self,
        user_id: str,
        query: str,
        top_k: int,
        filters: Optional[RetrievalFilter],
        db: Session
    ) -> List[Tuple[MemoryChunk, float]]:
        """
        Performs keyword search over MemoryChunk records and metadata.
        Strictly scoped by user_id.
        """
        if not user_id or not query.strip():
            return []

        # Tokenize query
        clean_q = re.sub(r'[^\w\s]', ' ', query.lower())
        tokens = [t for t in clean_q.split() if len(t) > 1 and t not in STOP_WORDS]
        if not tokens:
            tokens = [t for t in clean_q.split() if len(t) > 1]
        if not tokens:
            return []

        chunks = db.query(MemoryChunk).filter(MemoryChunk.user_id == user_id).all()
        scored_chunks: List[Tuple[MemoryChunk, float]] = []

        for chunk in chunks:
            if not self._matches_metadata_filters(chunk, filters):
                continue

            text = (chunk.chunk_text or "").lower()
            meta = chunk.metadata_info or {}
            title = str(meta.get("title", "")).lower()
            category = str(meta.get("category", "")).lower()
            entities = [str(e).lower() for e in meta.get("entities", [])]

            score = 0.0
            matched_terms = 0

            for token in tokens:
                token_matched = False
                # Exact word or substring matches in chunk body
                if token in text:
                    count = text.count(token)
                    score += 1.0 + min(count * 0.2, 1.0)
                    token_matched = True

                # Title match bonus
                if token in title:
                    score += 1.5
                    token_matched = True

                # Category match bonus
                if token in category:
                    score += 0.8
                    token_matched = True

                # Entity match bonus
                if any(token in ent for ent in entities):
                    score += 1.5
                    token_matched = True

                # Multimodal modality match bonus
                input_type = str(meta.get("input_type", "")).lower()
                if token in ["photo", "picture", "image", "visual"] and (input_type == "photo" or meta.get("has_photo")):
                    score += 1.2
                    token_matched = True
                if token in ["voice", "audio", "recording", "speech", "transcript"] and (input_type == "voice" or meta.get("has_voice")):
                    score += 1.2
                    token_matched = True
                if token in ["ocr", "scanned", "document", "slide", "presentation"] and (meta.get("has_ocr") or input_type == "photo"):
                    score += 1.2
                    token_matched = True

                if token_matched:
                    matched_terms += 1

            if score > 0.0:
                # Term coverage ratio boost
                coverage = matched_terms / len(tokens)
                final_score = (score / (len(tokens) * 3.0)) * (0.5 + 0.5 * coverage)
                normalized_score = min(1.0, round(final_score, 4))
                scored_chunks.append((chunk, normalized_score))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    # -------------------------------------------------------------------------
    # 4. HYBRID RANKING (RRF) & DEDUPLICATION
    # -------------------------------------------------------------------------
    @staticmethod
    def _reciprocal_rank_fusion(
        vector_results: List[Tuple[MemoryChunk, float]],
        keyword_results: List[Tuple[MemoryChunk, float]],
        rrf_k: int = 60,
        vector_weight: float = 1.0,
        keyword_weight: float = 0.8
    ) -> List[RetrievedChunk]:
        """
        Combines vector and keyword rankings using Reciprocal Rank Fusion (RRF).
        """
        chunk_map: Dict[str, MemoryChunk] = {}
        vector_scores: Dict[str, float] = {}
        keyword_scores: Dict[str, float] = {}
        rrf_scores: Dict[str, float] = {}

        # 1. Vector ranks
        for rank, (chunk, v_score) in enumerate(vector_results, start=1):
            chunk_id = chunk.id
            chunk_map[chunk_id] = chunk
            vector_scores[chunk_id] = v_score
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (vector_weight / (rrf_k + rank))

        # 2. Keyword ranks
        for rank, (chunk, k_score) in enumerate(keyword_results, start=1):
            chunk_id = chunk.id
            chunk_map[chunk_id] = chunk
            keyword_scores[chunk_id] = k_score
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (keyword_weight / (rrf_k + rank))

        if not rrf_scores:
            return []

        # Normalize RRF scores
        max_possible_rrf = (vector_weight / (rrf_k + 1)) + (keyword_weight / (rrf_k + 1))
        fused_results: List[RetrievedChunk] = []

        for chunk_id, raw_rrf in rrf_scores.items():
            chunk = chunk_map[chunk_id]
            norm_score = min(1.0, raw_rrf / max_possible_rrf)
            v_score = vector_scores.get(chunk_id, 0.0)
            k_score = keyword_scores.get(chunk_id, 0.0)

            # Combined explainable score
            combined_score = round(0.5 * norm_score + 0.35 * v_score + 0.15 * k_score, 4)

            meta = chunk.metadata_info or {}
            fused_results.append(RetrievedChunk(
                chunk_id=chunk.id,
                entry_id=chunk.diary_entry_id,
                user_id=chunk.user_id,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.chunk_text,
                score=combined_score,
                vector_score=round(v_score, 4) if chunk_id in vector_scores else None,
                keyword_score=round(k_score, 4) if chunk_id in keyword_scores else None,
                entry_date=meta.get("entry_date"),
                title=meta.get("title"),
                category=meta.get("category"),
                mood=meta.get("mood"),
                metadata=meta
            ))

        fused_results.sort(key=lambda x: x.score, reverse=True)
        return fused_results

    @staticmethod
    def _deduplicate_by_entry(
        chunks: List[RetrievedChunk],
        max_chunks_per_entry: int = 1
    ) -> List[RetrievedChunk]:
        """
        Deduplicates chunks belonging to the same DiaryEntry to promote memory diversity.
        """
        entry_counts: Dict[str, int] = {}
        deduped: List[RetrievedChunk] = []

        for c in chunks:
            count = entry_counts.get(c.entry_id, 0)
            if count < max_chunks_per_entry:
                deduped.append(c)
                entry_counts[c.entry_id] = count + 1

        return deduped

    # -------------------------------------------------------------------------
    # 5. PUBLIC RETRIEVAL PIPELINE
    # -------------------------------------------------------------------------
    async def retrieve_memories(
        self,
        user_id: str,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[RetrievalFilter] = None,
        min_score: Optional[float] = None,
        deduplicate: Optional[bool] = None,
        db: Optional[Session] = None
    ) -> RetrievalResponse:
        """
        Full end-to-end hybrid retrieval pipeline:
        1. Validate query & user isolation
        2. Generate query vector embedding
        3. Execute vector search & keyword search
        4. Hybrid RRF fusion
        5. Entry-level deduplication
        6. Minimum relevance thresholding
        7. Return structured RetrievalResponse
        """
        if not user_id or not query or not query.strip():
            return RetrievalResponse(query=query or "", total_retrieved=0, results=[])

        k = top_k or settings.RAG_TOP_K
        threshold = min_score if min_score is not None else settings.RAG_MIN_RELEVANCE_SCORE
        should_dedup = deduplicate if deduplicate is not None else settings.RAG_DEDUPLICATE_ENTRIES

        own_session = False
        if db is None:
            from app.core.database import SessionLocal
            db = SessionLocal()
            own_session = True

        try:
            # 1. Generate Query Vector Embedding
            query_embedding = await embedding_service.generate_embedding(query.strip())

            # 2. Parallel Vector & Keyword Searches
            candidate_k = max(k * 3, 15)
            vector_matches = await self.vector_search(
                user_id=user_id,
                query_embedding=query_embedding,
                top_k=candidate_k,
                filters=filters,
                db=db
            )
            keyword_matches = self.keyword_search(
                user_id=user_id,
                query=query.strip(),
                top_k=candidate_k,
                filters=filters,
                db=db
            )

            # 3. Hybrid Fusion (RRF)
            fused_chunks = self._reciprocal_rank_fusion(
                vector_results=vector_matches,
                keyword_results=keyword_matches,
                rrf_k=settings.RAG_RRF_K
            )

            # 4. Deduplication
            if should_dedup:
                final_chunks = self._deduplicate_by_entry(fused_chunks, max_chunks_per_entry=1)
            else:
                final_chunks = fused_chunks

            # 5. Apply Relevance Thresholding
            relevant_chunks = [
                c for c in final_chunks
                if (c.score >= threshold or (c.vector_score is not None and c.vector_score >= threshold))
            ]

            # 6. Slice to top_k
            results = relevant_chunks[:k]

            return RetrievalResponse(
                query=query.strip(),
                total_retrieved=len(results),
                results=results
            )

        except Exception as e:
            logger.error(f"Retrieval failed for user {user_id} with query '{query}': {e}", exc_info=True)
            return RetrievalResponse(query=query, total_retrieved=0, results=[])

        finally:
            if own_session:
                db.close()


retrieval_service = RetrievalService()

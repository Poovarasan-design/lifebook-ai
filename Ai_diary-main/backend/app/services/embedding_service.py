import re
import math
import uuid
import logging
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.diary import DiaryEntry
from app.models.embedding import MemoryChunk

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Embedding & Memory Indexing Service for LifeBook RAG.
    
    Provides:
    - Lightweight, zero-heavy-download deterministic vector embedding generator
    - Optional cloud/API embedding provider integration (OpenRouter/OpenAI)
    - Journal-aware chunking preserving rich narrative context & metadata
    - Atomic indexing & re-indexing scoped strictly to user_id + diary_entry_id
    - Safe deletion and fault-tolerant durability
    """

    def __init__(self):
        self.dim = settings.EMBEDDING_DIM

    # -------------------------------------------------------------------------
    # 1. EMBEDDING GENERATION
    # -------------------------------------------------------------------------
    def _generate_local_embedding(self, text: str) -> List[float]:
        """
        Lightweight deterministic semantic-hash embedding.
        Uses multi-token and character n-gram hashing with positional weighting
        projected into an N-dimensional space and L2-normalized.
        
        Guarantees:
        - 0MB model downloads (runs everywhere instantly)
        - Deterministic: identical input always produces identical vector
        - Semantic signal: overlapping vocabulary & n-grams share cosine similarity
        - Unit length: sum(v_i^2) == 1.0
        """
        dim = self.dim
        vec = [0.0] * dim
        cleaned = re.sub(r'[^\w\s]', ' ', text.lower()).strip()
        tokens = cleaned.split()
        
        if not tokens:
            # Uniform unit vector for empty/blank
            val = 1.0 / math.sqrt(dim)
            return [val] * dim

        # 1. Word token projections
        for i, word in enumerate(tokens):
            weight = 1.0 / (1.0 + 0.05 * math.log(i + 1))
            # Hash word into multiple vector indices
            h1 = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx1 = h1 % dim
            sign1 = 1.0 if ((h1 >> 8) & 1) else -1.0
            vec[idx1] += sign1 * weight * 1.5

            # Word bigram context
            if i > 0:
                bigram = f"{tokens[i-1]}_{word}"
                h_bi = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
                idx_bi = h_bi % dim
                sign_bi = 1.0 if ((h_bi >> 8) & 1) else -1.0
                vec[idx_bi] += sign_bi * weight * 1.0

        # 2. Character 3-grams for subword similarity
        for i in range(len(cleaned) - 2):
            trigram = cleaned[i:i+3]
            h_tri = int(hashlib.md5(trigram.encode("utf-8")).hexdigest(), 16)
            idx_tri = h_tri % dim
            sign_tri = 1.0 if ((h_tri >> 4) & 1) else -1.0
            vec[idx_tri] += sign_tri * 0.3

        # L2 Normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            vec = [x / norm for x in vec]
        else:
            val = 1.0 / math.sqrt(dim)
            vec = [val] * dim

        return [round(x, 6) for x in vec]

    async def _generate_api_embedding(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Fetch embeddings from OpenRouter or OpenAI API if configured.
        """
        api_key = settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            return None

        url = "https://openrouter.ai/api/v1/embeddings" if settings.OPENROUTER_API_KEY else "https://api.openai.com/v1/embeddings"
        model = settings.EMBEDDING_MODEL if settings.EMBEDDING_MODEL else "text-embedding-3-small"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": texts
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    embeddings = [item["embedding"] for item in data.get("data", [])]
                    if len(embeddings) == len(texts):
                        return embeddings
                else:
                    logger.warning(f"Embedding API returned status {response.status_code}: {response.text[:200]}")
        except Exception as e:
            logger.warning(f"Embedding API call failed, using local fallback: {e}")

        return None

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text.
        """
        if settings.EMBEDDING_PROVIDER in ["openrouter", "openai"] and (settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY):
            api_res = await self._generate_api_embedding([text])
            if api_res and len(api_res) > 0:
                return api_res[0]
        return self._generate_local_embedding(text)

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for multiple texts.
        """
        if not texts:
            return []

        if settings.EMBEDDING_PROVIDER in ["openrouter", "openai"] and (settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY):
            api_res = await self._generate_api_embedding(texts)
            if api_res and len(api_res) == len(texts):
                return api_res

        return [self._generate_local_embedding(t) for t in texts]

    # -------------------------------------------------------------------------
    # 2. JOURNAL-AWARE CHUNKING
    # -------------------------------------------------------------------------
    @staticmethod
    def extract_canonical_text(entry: DiaryEntry) -> Optional[str]:
        """
        Resolves multimodal canonical text combining:
        1. generated_content / raw_text
        2. voice transcript
        3. image OCR text
        """
        parts = []
        if entry.generated_content and entry.generated_content.strip():
            parts.append(entry.generated_content.strip())
        elif entry.raw_text and entry.raw_text.strip():
            parts.append(entry.raw_text.strip())

        if entry.transcript and entry.transcript.strip():
            t = entry.transcript.strip()
            if not any(t in p for p in parts):
                parts.append(f"Voice Transcript: {t}")

        if getattr(entry, "ocr_text", None) and entry.ocr_text.strip():
            ocr = entry.ocr_text.strip()
            if not any(ocr in p for p in parts):
                parts.append(f"Image Text / OCR: {ocr}")

        if parts:
            return "\n\n".join(parts)
        return None

    def chunk_memory(self, entry: DiaryEntry) -> List[Dict[str, Any]]:
        """
        Splits a diary entry into journal-aware semantic chunks with attached metadata.
        Preserves complete paragraphs, emotional context, multimodal tags, and entity references.
        """
        text = self.extract_canonical_text(entry)
        if not text:
            return []

        # Gather metadata
        entry_date_str = entry.entry_date.isoformat() if entry.entry_date else datetime.now(timezone.utc).isoformat()
        entity_names = []
        if hasattr(entry, "entities") and entry.entities:
            entity_names = [e.name for e in entry.entities if hasattr(e, "name") and e.name]

        has_photo = bool(
            entry.photo_urls or 
            entry.input_type == "photo" or 
            (entry.media_path and any(str(entry.media_path).endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]))
        )
        has_voice = bool(entry.input_type == "voice" or entry.transcript)
        has_ocr = bool(getattr(entry, "ocr_text", None))

        base_metadata = {
            "entry_id": entry.id,
            "user_id": entry.user_id,
            "entry_date": entry_date_str,
            "title": entry.title or "Untitled Memory",
            "category": entry.category or "General",
            "mood": entry.mood or "reflective",
            "entities": entity_names,
            "input_type": entry.input_type or "text",
            "has_photo": has_photo,
            "has_voice": has_voice,
            "has_ocr": has_ocr,
            "photo_urls": list(entry.photo_urls or [])
        }

        # Chunking strategy:
        # If text is small (< 600 characters), keep as a single coherent chunk
        if len(text) <= 600:
            return [{
                "chunk_index": 0,
                "chunk_text": text,
                "metadata_info": {**base_metadata, "chunk_index": 0}
            }]

        # Split into paragraphs or sentences for longer entries
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks_text: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            if not current_chunk:
                current_chunk = para
            elif len(current_chunk) + len(para) + 2 <= 600:
                current_chunk += "\n\n" + para
            else:
                chunks_text.append(current_chunk)
                current_chunk = para

        if current_chunk:
            chunks_text.append(current_chunk)

        # If splitting by paragraph produced a single huge chunk (> 800 chars), split by sentences
        final_chunks: List[str] = []
        for c in chunks_text:
            if len(c) > 800:
                sentences = re.split(r'(?<=[.!?])\s+', c)
                sub_chunk = ""
                for s in sentences:
                    if not sub_chunk:
                        sub_chunk = s
                    elif len(sub_chunk) + len(s) + 1 <= 500:
                        sub_chunk += " " + s
                    else:
                        final_chunks.append(sub_chunk)
                        sub_chunk = s
                if sub_chunk:
                    final_chunks.append(sub_chunk)
            else:
                final_chunks.append(c)

        # Build chunk dictionaries
        result = []
        for idx, chunk_str in enumerate(final_chunks):
            if chunk_str.strip():
                result.append({
                    "chunk_index": idx,
                    "chunk_text": chunk_str.strip(),
                    "metadata_info": {
                        **base_metadata,
                        "chunk_index": idx
                    }
                })

        return result

    # -------------------------------------------------------------------------
    # 3. INDEXING & LIFECYCLE MANAGEMENT
    # -------------------------------------------------------------------------
    async def index_memory(self, entry: DiaryEntry, db: Session) -> bool:
        """
        Indexes a diary entry into MemoryChunk records:
        1. Atomically removes any old chunks for this entry_id + user_id
        2. Chunks the canonical text
        3. Generates embeddings
        4. Persists new MemoryChunk records
        
        Durability Guarantee:
        - If indexing fails, the original DiaryEntry is untouched.
        """
        if not entry or not entry.id or not entry.user_id:
            return False

        try:
            # 1. Remove existing chunks for this specific entry and user (strict isolation)
            db.query(MemoryChunk).filter(
                MemoryChunk.diary_entry_id == entry.id,
                MemoryChunk.user_id == entry.user_id
            ).delete(synchronize_session=False)

            # 2. Chunk memory text
            chunks = self.chunk_memory(entry)
            if not chunks:
                db.commit()
                return False

            # 3. Generate embeddings
            texts = [c["chunk_text"] for c in chunks]
            embeddings = await self.generate_embeddings(texts)

            # 4. Create MemoryChunk objects
            chunk_records = []
            for i, chunk in enumerate(chunks):
                emb = embeddings[i] if i < len(embeddings) else self._generate_local_embedding(chunk["chunk_text"])
                chunk_obj = MemoryChunk(
                    id=str(uuid.uuid4()),
                    user_id=entry.user_id,
                    diary_entry_id=entry.id,
                    chunk_index=chunk["chunk_index"],
                    chunk_text=chunk["chunk_text"],
                    embedding=emb,
                    metadata_info=chunk["metadata_info"]
                )
                chunk_records.append(chunk_obj)

            db.add_all(chunk_records)
            db.commit()
            logger.info(f"Successfully indexed {len(chunk_records)} chunks for entry {entry.id} (user {entry.user_id})")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to index memory for entry {entry.id}: {e}", exc_info=True)
            return False

    def delete_memory_index(self, entry_id: str, user_id: str, db: Session) -> bool:
        """
        Removes all memory chunks for a given entry_id and user_id.
        Strictly scopes deletion to the authenticated user.
        """
        try:
            deleted_count = db.query(MemoryChunk).filter(
                MemoryChunk.diary_entry_id == entry_id,
                MemoryChunk.user_id == user_id
            ).delete(synchronize_session=False)
            db.commit()
            logger.info(f"Deleted {deleted_count} memory chunks for entry {entry_id} (user {user_id})")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete memory index for entry {entry_id}: {e}", exc_info=True)
            return False


embedding_service = EmbeddingService()

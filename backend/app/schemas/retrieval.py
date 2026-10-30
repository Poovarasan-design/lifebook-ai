from __future__ import annotations
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class RetrievalFilter(BaseModel):
    """Optional metadata filters applied to restrict retrieval scope."""

    date_from: Optional[datetime] = Field(
        default=None,
        description="Restrict results to entries on or after this datetime."
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="Restrict results to entries on or before this datetime."
    )
    category: Optional[str] = Field(
        default=None,
        description="Filter by diary category (e.g. 'Work', 'Health', 'Personal')."
    )
    mood: Optional[str] = Field(
        default=None,
        description="Filter by mood label (e.g. 'happy', 'reflective')."
    )
    entities: Optional[List[str]] = Field(
        default=None,
        description="Filter by entity names (people, places, projects). At least one must match."
    )


class RetrievalRequest(BaseModel):
    """Request body for POST /api/v1/search/retrieve."""

    query: str = Field(..., min_length=1, description="Natural language question to retrieve memories for.")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of results to return.")
    filters: Optional[RetrievalFilter] = Field(default=None, description="Optional metadata filters.")
    min_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Minimum relevance score threshold (0.0-1.0). Overrides server default if set."
    )
    deduplicate: Optional[bool] = Field(
        default=None,
        description="Whether to deduplicate chunks from the same diary entry. Uses server default if None."
    )


class RetrievedChunk(BaseModel):
    """A single retrieved memory chunk with relevance scores and source attribution."""

    chunk_id: str = Field(description="Unique ID of the MemoryChunk.")
    entry_id: str = Field(description="ID of the parent DiaryEntry.")
    user_id: str = Field(description="User ID — always the authenticated requester.")
    chunk_index: int = Field(description="Position of this chunk within its parent entry.")
    chunk_text: str = Field(description="The text content of this memory chunk.")

    # Relevance scoring — explainable hybrid scores
    score: float = Field(description="Combined hybrid relevance score (0.0-1.0).")
    vector_score: Optional[float] = Field(default=None, description="Raw cosine similarity from vector search.")
    keyword_score: Optional[float] = Field(default=None, description="Normalized keyword relevance score.")

    # Source entry attribution
    entry_date: Optional[str] = Field(default=None, description="ISO date string of the source diary entry.")
    title: Optional[str] = Field(default=None, description="Title of the source diary entry.")
    category: Optional[str] = Field(default=None, description="Category of the source diary entry.")
    mood: Optional[str] = Field(default=None, description="Mood recorded in the source diary entry.")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Full chunk metadata (entities, entry_id, user_id, etc.)."
    )


class RetrievalResponse(BaseModel):
    """Structured retrieval response with ranked, deduplicated memory results."""

    query: str = Field(description="The original user query.")
    total_retrieved: int = Field(description="Number of results after thresholding and deduplication.")
    results: List[RetrievedChunk] = Field(
        default_factory=list,
        description="Ranked list of relevant memory chunks, best first."
    )

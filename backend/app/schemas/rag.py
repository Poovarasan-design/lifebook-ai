from __future__ import annotations
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class RAGSource(BaseModel):
    citation: str
    entry_id: str
    chunk_id: str
    title: Optional[str] = None
    date: Optional[str] = None
    snippet: Optional[str] = None
    score: float
    category: Optional[str] = None
    mood: Optional[str] = None

class RAGAnswer(BaseModel):
    query: str
    answer: str
    sources: List[RAGSource] = []
    retrieved_count: int = 0
    is_grounded: bool = True
    source_entry_id: Optional[str] = None
    related_entries: List[Dict[str, Any]] = []
    related_entities: List[str] = []
    forgetting_items: List[Dict[str, Any]] = []

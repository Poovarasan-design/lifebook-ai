from __future__ import annotations
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from datetime import datetime

class SearchQuery(BaseModel):
    query: str

class SearchResultItem(BaseModel):
    entry_id: str
    title: str
    snippet: str
    category: str
    date: datetime
    score: float
    matched_entities: List[str] = []

class ForgettingItem(BaseModel):
    id: str
    title: str
    description: str
    due_date: Optional[str] = None
    priority: str
    source_entry_id: Optional[str] = None
    days_ago_mentioned: int = 0
    reason: str

class ConversationalAnswer(BaseModel):
    query: str
    answer: str
    source_entry_id: Optional[str] = None
    related_entries: List[SearchResultItem] = []
    related_entities: List[str] = []
    forgetting_items: List[ForgettingItem] = []


class ForgettingResponse(BaseModel):
    headline: str
    items: List[ForgettingItem]

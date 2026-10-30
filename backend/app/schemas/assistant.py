from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class ProactiveItem(BaseModel):
    id: str
    title: str
    description: str
    priority: str  # HIGH, MEDIUM, LOW
    category: str  # overdue, due_soon, upcoming, stale, routine_deviation, unresolved, observation
    due_date: Optional[str] = None
    resolved_due_date: Optional[str] = None
    source_entry_id: Optional[str] = None
    days_ago: Optional[int] = None
    action_label: Optional[str] = None
    extra_data: Dict[str, Any] = {}

class TodayAssistantResponse(BaseModel):
    date: str
    greeting: str
    needs_attention: List[ProactiveItem] = []
    upcoming: List[ProactiveItem] = []
    routine_changes: List[ProactiveItem] = []
    reminders: List[Dict[str, Any]] = []
    insights: List[str] = []
    is_empty: bool = True

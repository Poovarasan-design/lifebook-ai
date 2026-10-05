from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class RoutineOut(BaseModel):
    id: str
    user_id: str
    title: str
    activity: str
    location: Optional[str] = None
    pattern: str
    frequency: str
    details: Optional[str] = None
    occurrence_count: int
    confidence: float
    last_observed: datetime
    is_active: bool
    deviation_prompt: Optional[str] = None
    deviation_active: bool

    class Config:
        from_attributes = True

class RoutineDeviationAction(BaseModel):
    action: str  # "changed", "skipped", "disable_routine"
    note: Optional[str] = None

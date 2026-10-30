from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class CommitmentOut(BaseModel):
    id: str
    user_id: str
    diary_entry_id: Optional[str] = None
    description: str
    project: Optional[str] = None
    due_date: Optional[str] = None
    confidence: float
    status: str  # PENDING, COMPLETED, RESCHEDULED, DISMISSED
    priority: str
    activity_thread: Optional[str] = None
    next_action: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CommitmentCreate(BaseModel):
    description: str
    project: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = "high"

class CommitmentUpdate(BaseModel):
    description: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

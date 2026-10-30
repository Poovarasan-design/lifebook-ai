from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class StatusEvent(BaseModel):
    status: str
    timestamp: str
    progress: int
    message: str

class DiaryEntryCreate(BaseModel):
    raw_text: str
    title: Optional[str] = None
    category: Optional[str] = "General"
    mood: Optional[str] = None
    entry_date: Optional[datetime] = None

class DiaryEntryOut(BaseModel):
    id: str
    user_id: str
    input_type: str
    title: Optional[str] = None
    raw_text: Optional[str] = None
    transcript: Optional[str] = None
    media_path: Optional[str] = None
    photo_urls: List[str] = []
    ocr_text: Optional[str] = None
    generated_content: Optional[str] = None
    category: str
    mood: Optional[str] = None
    status: str
    confidence: float
    status_history: List[Dict[str, Any]] = []
    disambiguation: Optional[Dict[str, Any]] = None
    entry_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DiaryConfirmRequest(BaseModel):
    confirmed_title: Optional[str] = None
    confirmed_content: Optional[str] = None
    category: Optional[str] = None
    disambiguation_resolution: Optional[Dict[str, str]] = None  # e.g., {"Ravi": "Ravi Kumar"}

class DiaryEntryUpdate(BaseModel):
    title: Optional[str] = None
    generated_content: Optional[str] = None
    category: Optional[str] = None
    mood: Optional[str] = None

class DiaryRegenerateRequest(BaseModel):
    tone: Optional[str] = "reflective"
    instructions: Optional[str] = None

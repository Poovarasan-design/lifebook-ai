from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class ExtractedEntity(BaseModel):
    type: str  # person, place, project, activity
    name: str
    confidence: float = 0.95
    attributes: Dict[str, Any] = {}

class ExtractedCommitment(BaseModel):
    description: str
    project: Optional[str] = None
    due_date: Optional[str] = None
    confidence: float = 0.90
    priority: str = "high"
    activity_thread: Optional[str] = None
    next_action: Optional[str] = None
    person: Optional[str] = None
    target_date: Optional[str] = None  # YYYY-MM-DD

class AIUnderstandingResult(BaseModel):
    title: str
    diary_draft: str
    category: str
    mood: Optional[str] = "reflective"
    people: List[ExtractedEntity] = []
    places: List[ExtractedEntity] = []
    projects: List[ExtractedEntity] = []
    activities: List[ExtractedEntity] = []
    commitments: List[ExtractedCommitment] = []
    tags: List[str] = []
    confidence: float = 0.95
    disambiguation: Optional[Dict[str, Any]] = None

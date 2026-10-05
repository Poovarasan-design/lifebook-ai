from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # "User", "Person", "Place", "Project", "Commitment", "Activity", "Memory"
    attributes: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str  # "met", "visited", "worked_on", "requires", "scheduled_for", "involves", "took_place_at", "relates_to"
    confidence: float = 0.95

class LifeGraphOut(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class EntityTimelineItem(BaseModel):
    entry_id: str
    date: Optional[str] = None
    title: str
    snippet: Optional[str] = None
    category: Optional[str] = None
    photos: List[str] = []
    relation: Optional[str] = None

class EntityCommitmentSummary(BaseModel):
    id: str
    description: str
    status: str
    due_date: Optional[str] = None
    priority: Optional[str] = None

class EntityRelationshipItem(BaseModel):
    target_name: str
    target_type: str
    relationship: str
    confidence: float = 0.95

class EntityConflictItem(BaseModel):
    issue_type: str
    description: str
    severity: str = "low"  # "low", "medium", "high"

class EntityHistoryOut(BaseModel):
    name: str
    type: str  # "person", "place", "project", "activity"
    count: int
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    timeline: List[EntityTimelineItem] = []
    related_entities: Dict[str, List[str]] = {}
    commitments: List[EntityCommitmentSummary] = []
    relationships: List[EntityRelationshipItem] = []
    conflicts: List[EntityConflictItem] = []

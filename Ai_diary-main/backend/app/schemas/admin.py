from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class SystemMetrics(BaseModel):
    total_users: int
    total_entries: int
    total_commitments: int
    active_routines: int
    avg_processing_latency_ms: float
    ai_success_rate: float
    stt_success_rate: float
    queue_depth: int
    failed_jobs_count: int
    routine_false_positive_rate: float

class AuditLogOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    actor: str
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

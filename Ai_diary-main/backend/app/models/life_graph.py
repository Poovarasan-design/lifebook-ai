import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from app.core.database import Base

class LifeGraphRelationship(Base):
    __tablename__ = "life_graph_relationships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    diary_entry_id = Column(String(36), ForeignKey("diary_entries.id", ondelete="SET NULL"), nullable=True)

    source_type = Column(String(50), nullable=False)   # "User", "Person", "Project", "Place"
    source_name = Column(String(255), nullable=False, index=True)
    target_type = Column(String(50), nullable=False)   # "Person", "Project", "Commitment", "Place"
    target_name = Column(String(255), nullable=False, index=True)
    relationship_type = Column(String(100), nullable=False, index=True)  # "visited", "met", "worked_on", "requires", "scheduled_for"
    
    confidence = Column(Float, default=0.95)
    metadata_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


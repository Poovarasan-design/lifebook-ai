import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Entity(Base):
    __tablename__ = "entities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    diary_entry_id = Column(String(36), ForeignKey("diary_entries.id", ondelete="CASCADE"), nullable=True, index=True)
    
    type = Column(String(50), nullable=False, index=True)  # "person", "place", "activity", "project", "category"
    name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=False, index=True)
    confidence = Column(Float, default=0.95)
    attributes = Column(JSON, default=dict)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="entities")
    entry = relationship("DiaryEntry", back_populates="entities")

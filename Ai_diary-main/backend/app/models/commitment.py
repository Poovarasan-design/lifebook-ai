import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Commitment(Base):
    __tablename__ = "commitments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    diary_entry_id = Column(String(36), ForeignKey("diary_entries.id", ondelete="SET NULL"), nullable=True)

    description = Column(String(500), nullable=False)
    project = Column(String(255), nullable=True)
    due_date = Column(String(100), nullable=True)  # e.g., "Next Wednesday", "2026-09-16", "Tomorrow"
    resolved_due_date = Column(DateTime, nullable=True)
    confidence = Column(Float, default=0.90)
    
    status = Column(String(50), default="PENDING", index=True)
    priority = Column(String(20), default="high")
    activity_thread = Column(String(255), nullable=True)
    next_action = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="commitments")
    entry = relationship("DiaryEntry", back_populates="commitments")

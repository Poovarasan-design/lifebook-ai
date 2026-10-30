import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Routine(Base):
    __tablename__ = "routines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)      # e.g., "Friday Lunch"
    activity = Column(String(255), nullable=False)   # e.g., "Lunch at ABC Restaurant"
    location = Column(String(255), nullable=True)    # e.g., "ABC Restaurant"
    pattern = Column(String(100), nullable=False)    # e.g., "Friday"
    frequency = Column(String(50), default="weekly")
    details = Column(String(255), default="Sambar Rice")
    occurrence_count = Column(Integer, default=4)
    confidence = Column(Float, default=0.87)
    
    last_observed = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    disabled_reason = Column(String(255), nullable=True)
    non_response_count = Column(Integer, default=0)
    
    # Deviation information if system noticed a change
    deviation_prompt = Column(String(500), nullable=True)
    deviation_active = Column(Boolean, default=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="routines")

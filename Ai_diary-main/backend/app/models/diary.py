import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    input_type = Column(String(20), nullable=False)  # "text", "voice", "photo"
    title = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    media_path = Column(String(500), nullable=True)  # Audio or primary photo path
    photo_urls = Column(JSON, default=list)          # List of attached photos
    ocr_text = Column(Text, nullable=True)           # Extracted OCR text from attached image
    generated_content = Column(Text, nullable=True)
    category = Column(String(100), default="General")
    mood = Column(String(50), nullable=True)
    
    # 11-stage status machine:
    # RECEIVED, SAVED, TRANSCRIBING, EXTRACTING, DRAFTED, USER_REVIEW, CONFIRMED, GRAPH_UPDATED, EMBEDDING_CREATED, INDEXED, COMPLETED
    # Or: FAILED, ENRICHMENT_PENDING
    status = Column(String(50), default="RECEIVED", index=True)
    confidence = Column(Float, default=1.0)
    
    # Timestamps & status history
    status_history = Column(JSON, default=list)  # [{"status": "RECEIVED", "timestamp": "...", "progress": 10, "message": "..."}]
    disambiguation = Column(JSON, nullable=True)  # e.g., {"entity": "Ravi", "options": ["Ravi Kumar", "Ravi S", "Neither"]}
    
    entry_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="entries")
    entities = relationship("Entity", back_populates="entry", cascade="all, delete-orphan")
    commitments = relationship("Commitment", back_populates="entry", cascade="all, delete-orphan")
    chunks = relationship("MemoryChunk", back_populates="entry", cascade="all, delete-orphan")

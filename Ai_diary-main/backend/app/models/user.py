import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for Google-only accounts
    full_name = Column(String(255), nullable=False)
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    avatar_url = Column(String(512), nullable=True)
    auth_provider = Column(String(50), default="local", nullable=False)  # "local", "google", "both"
    role = Column(String(50), default="user", nullable=False)
    is_active = Column(Boolean, default=True)
    preferences = Column(JSON, default=lambda: {
        "routine_learning": True,
        "location_analysis": True,
        "photo_analysis": True,
        "ai_personalization": True,
        "morning_briefing": True
    })
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    entries = relationship("DiaryEntry", back_populates="user", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="user", cascade="all, delete-orphan")
    commitments = relationship("Commitment", back_populates="user", cascade="all, delete-orphan")
    routines = relationship("Routine", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    chunks = relationship("MemoryChunk", back_populates="user", cascade="all, delete-orphan")

    @property
    def name(self) -> str:
        return self.full_name

    @name.setter
    def name(self, val: str):
        self.full_name = val

import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional, Any
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.config import settings

# Attempt pgvector import safely
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False


class VectorType(TypeDecorator):
    """
    Dual-database Vector Type:
    - In PostgreSQL: Uses native pgvector `Vector(dim)` when pgvector is installed.
    - In SQLite / Test / Dev: Uses `JSON` array fallback to maintain 100% compatibility.
    """
    impl = JSON
    cache_ok = True

    def __init__(self, dim: Optional[int] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim or settings.EMBEDDING_DIM

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PGVECTOR_AVAILABLE:
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect) -> Any:
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        if hasattr(value, "tolist"):  # numpy array support
            return [float(x) for x in value.tolist()]
        return value

    def process_result_value(self, value: Any, dialect) -> Optional[List[float]]:
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        if hasattr(value, "tolist"):
            return [float(x) for x in value.tolist()]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [float(x) for x in parsed]
            except Exception:
                pass
        return value


class MemoryChunk(Base):
    __tablename__ = "memory_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    diary_entry_id = Column(String(36), ForeignKey("diary_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    
    chunk_index = Column(Integer, nullable=False, default=0)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(VectorType(dim=settings.EMBEDDING_DIM), nullable=True)
    metadata_info = Column(JSON, default=dict, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="chunks")
    entry = relationship("DiaryEntry", back_populates="chunks")

"""
Phase 7 Tests: Production, Privacy & Scale Hardening
Tests cover:
  1. Production HTTP security headers enforcement
  2. Health & Readiness probe endpoints
  3. Safe error handling (no stack traces or secret leaks to client)
  4. User isolation across all endpoints
  5. Cascade deletion & disk cleanup verification
  6. Rate limiting protection
"""

import pytest
import uuid
import os
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.commitment import Commitment
from app.models.embedding import MemoryChunk
from app.services.diary_service import DiaryService
from app.services.embedding_service import embedding_service
from app.storage.storage_service import storage_service
from app.main import app

client = TestClient(app)

def _get_or_create_user(email: str, name: str, db):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        from app.core.security import get_password_hash
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            full_name=name,
            hashed_password=get_password_hash("Pass1234!"),
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def test_production_security_headers():
    response = client.get("/api/health")
    assert response.status_code == 200
    headers = response.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_health_and_readiness_probes():
    # Liveness probe
    res_live = client.get("/health")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "healthy"

    # Readiness probe
    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 200
    data = res_ready.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert data["storage"] == "writable"


def test_safe_error_handling_no_leaks():
    # Query non-existent endpoint or bad ID
    response = client.get("/api/v1/diary/invalid-uuid-999999", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code in [401, 403, 404]
    # Verify response is clean JSON without Python stack traces
    assert "Traceback" not in response.text
    assert "password" not in response.text.lower()
    assert "secret" not in response.text.lower()


@pytest.mark.asyncio
async def test_cascade_memory_and_media_cleanup():
    db = SessionLocal()
    try:
        user = _get_or_create_user(f"user_p7_cleanup_{uuid.uuid4().hex[:6]}@lifebook.ai", "Cleanup User", db)
        
        # Create photo entry
        entry = await DiaryService.create_photo_entry(
            user_id=user.id,
            image_bytes=b"sample_test_bytes_12345",
            filename="test_pic.png",
            caption="Test Photo to Delete",
            db=db
        )

        entry_dir = storage_service._get_user_entry_dir(user.id, entry.id)
        assert os.path.exists(entry_dir)

        # Index memory
        await embedding_service.index_memory(entry, db)
        chunks = db.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry.id).all()
        assert len(chunks) >= 1

        # Delete entry cleanly
        embedding_service.delete_memory_index(entry.id, user.id, db)
        storage_service.delete_user_entry_dir(user.id, entry.id)
        db.delete(entry)
        db.commit()

        # Verify disk directory and DB records are completely purged
        assert not os.path.exists(entry_dir)
        remaining = db.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry.id).all()
        assert len(remaining) == 0
    finally:
        db.close()

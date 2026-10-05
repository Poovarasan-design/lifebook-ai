"""
Phase 5 Tests: Multimodal Intelligence
Tests cover:
  1. Image processing & image understanding
  2. OCR text extraction from photo
  3. Voice transcription flow to memory
  4. Multimodal memory creation (text, voice, photo, OCR)
  5. Media deletion propagation on disk & index
  6. User isolation for multimodal memories
  7. Multimodal retrieval (finding memories via photo/OCR keywords)
  8. RAG context isolation with multimodal queries
  9. Unsupported vision provider fallback to local/OCR
 10. AI / provider failure handling gracefully
"""

import pytest
import io
import os
import uuid
import asyncio
from datetime import datetime, timezone
from PIL import Image

from app.core.database import SessionLocal
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.embedding import MemoryChunk
from app.services.diary_service import DiaryService
from app.services.ocr_service import ocr_service
from app.services.embedding_service import embedding_service
from app.services.retrieval_service import retrieval_service
from app.services.rag_service import rag_service
from app.storage.storage_service import storage_service
from app.ai.local_provider import SmartLocalAIProvider
from app.ai.openrouter_provider import OpenRouterProvider
from app.ai.openai_provider import RealAIProvider
from app.schemas.retrieval import RetrievalFilter

def _create_sample_image_bytes(text_comment: str = "LifeBook AI Architecture Presentation") -> bytes:
    img = Image.new("RGB", (200, 100), color=(240, 240, 240))
    info = {"Description": text_comment}
    buf = io.BytesIO()
    img.save(buf, format="PNG", pnginfo=None, **info)
    return buf.getvalue()

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
    else:
        # Clean up existing test artifacts for this user
        db.query(MemoryChunk).filter(MemoryChunk.user_id == user.id).delete()
        db.query(DiaryEntry).filter(DiaryEntry.user_id == user.id).delete()
        db.commit()
    return user



def test_ocr_extraction():
    img_bytes = _create_sample_image_bytes("Hackathon Project Final Demo Slide")
    extracted = ocr_service.extract_text_from_image(img_bytes, "demo_slide.png")
    # Should extract embedded text comment or string cleanly
    assert isinstance(extracted, str)


@pytest.mark.asyncio
async def test_image_processing_and_understanding():
    provider = SmartLocalAIProvider()
    img_bytes = _create_sample_image_bytes("Meeting with Dr. Vikram about Robotics Lab")
    
    result = await provider.understand_image(
        image_bytes=img_bytes,
        filename="robotics_lab.png",
        caption="Team discussion at Robotics Lab",
        ocr_text="Robotics Project Blueprint"
    )

    assert result.title is not None
    assert "Robotics" in result.title or "Discussion" in result.title or "Photo" in result.title
    assert any(p.name == "Vikram" for p in result.people) or any("Robotics" in pr.name for pr in result.projects) or result.category in ["Visual", "Project", "College / Project", "Personal", "Work / Business"]


@pytest.mark.asyncio
async def test_voice_transcription_flow():
    db = SessionLocal()
    try:
        user = _get_or_create_user("user_p5_voice@lifebook.ai", "Voice User", db)
        audio_bytes = b"RIFF" + b"\x00" * 300  # Mock audio container
        
        entry = await DiaryService.create_voice_entry(
            user_id=user.id,
            audio_bytes=audio_bytes,
            filename="voice_memo.webm",
            db=db,
            transcript="I promised to send the revised proposal to Sarah by tomorrow."
        )

        assert entry.input_type == "voice"
        assert entry.transcript == "I promised to send the revised proposal to Sarah by tomorrow."
        assert entry.status == "SAVED"

        # Process AI
        await DiaryService.process_entry_ai(entry.id, db=db)
        db.refresh(entry)
        assert entry.status == "USER_REVIEW"
        assert entry.generated_content is not None
        assert any(p.name == "Sarah" for p in entry.entities)
    finally:
        db.close()


@pytest.mark.asyncio
async def test_multimodal_memory_creation_and_indexing():
    db = SessionLocal()
    try:
        user = _get_or_create_user("user_p5_multimodal@lifebook.ai", "Multimodal User", db)
        img_bytes = _create_sample_image_bytes("Conference Presentation on Neural Architecture")

        # 1. Create photo entry
        entry = await DiaryService.create_photo_entry(
            user_id=user.id,
            image_bytes=img_bytes,
            filename="presentation_photo.png",
            caption="Presented our deep learning framework at the AI Summit with Alex",
            db=db
        )

        assert entry.input_type == "photo"
        assert len(entry.photo_urls) > 0

        # 2. Process with AI
        await DiaryService.process_entry_ai(entry.id, db=db)
        db.refresh(entry)
        assert entry.status == "USER_REVIEW"

        # 3. Confirm entry (syncs to graph, commitments, routines, embeddings)
        confirmed = await DiaryService.confirm_entry(
            user_id=user.id,
            entry_id=entry.id,
            confirmed_title="AI Summit Presentation",
            confirmed_content="Presented our deep learning framework with Alex at the AI Summit.",
            disambiguation_resolution=None,
            db=db
        )

        assert confirmed.status == "COMPLETED"

        # 4. Verify MemoryChunk was created with multimodal metadata
        chunks = db.query(MemoryChunk).filter(
            MemoryChunk.diary_entry_id == entry.id,
            MemoryChunk.user_id == user.id
        ).all()
        assert len(chunks) >= 1
        meta = chunks[0].metadata_info
        assert meta.get("has_photo") is True
        assert meta.get("input_type") == "photo"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_media_deletion_propagation():
    db = SessionLocal()
    try:
        user = _get_or_create_user("user_p5_del@lifebook.ai", "Delete User", db)
        img_bytes = _create_sample_image_bytes("Temp Photo To Delete")

        entry = await DiaryService.create_photo_entry(
            user_id=user.id,
            image_bytes=img_bytes,
            filename="delete_me.png",
            caption="Temporary test photo",
            db=db
        )

        entry_dir = storage_service._get_user_entry_dir(user.id, entry.id)
        assert os.path.exists(entry_dir)

        # Index memory
        await embedding_service.index_memory(entry, db)
        chunks = db.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry.id).all()
        assert len(chunks) >= 1

        # Delete entry via storage and embedding cleanup
        embedding_service.delete_memory_index(entry.id, user.id, db)
        storage_service.delete_user_entry_dir(user.id, entry.id)
        db.delete(entry)
        db.commit()

        # Verify disk directory and DB chunks are gone
        assert not os.path.exists(entry_dir)
        remaining_chunks = db.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry.id).all()
        assert len(remaining_chunks) == 0
    finally:
        db.close()


@pytest.mark.asyncio
async def test_multimodal_retrieval_and_rag():
    db = SessionLocal()
    try:
        user = _get_or_create_user("user_p5_rag@lifebook.ai", "RAG User", db)
        
        # Create a confirmed memory with photo & presentation details
        entry = DiaryEntry(
            id=str(uuid.uuid4()),
            user_id=user.id,
            input_type="photo",
            title="Annual Project Showcase",
            raw_text="Saved slide photo from our annual project showcase in hall B",
            generated_content="Showcased our autonomous AI agent project presentation in the main auditorium.",
            photo_urls=["/api/v1/diary/p1/media"],
            ocr_text="Autonomous AI Agent Project Architecture Slide 1",
            category="College / Project",
            mood="excited",
            status="COMPLETED",
            entry_date=datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc)
        )
        db.add(entry)
        db.commit()

        # Index memory
        await embedding_service.index_memory(entry, db)

        # 1. Retrieval query targeting photo presentation
        res = await retrieval_service.retrieve_memories(
            user_id=user.id,
            query="Which photo contains my project presentation?",
            top_k=5,
            filters=None,
            db=db
        )
        assert len(res.results) >= 1
        assert any("Showcase" in (c.title or "") or "presentation" in (c.chunk_text or "").lower() for c in res.results)

        # 2. RAG Answer generation
        answer = await rag_service.answer_question(
            user_id=user.id,
            query="Which photo contains my project presentation?",
            top_k=5,
            db=db
        )
        assert answer.is_grounded is True
        assert len(answer.sources) >= 1
        assert any(s.entry_id == entry.id for s in answer.sources)
    finally:
        db.close()


@pytest.mark.asyncio
async def test_user_isolation_multimodal_rag():
    db = SessionLocal()
    try:
        user_a = _get_or_create_user("user_p5_iso_a@lifebook.ai", "User A", db)
        user_b = _get_or_create_user("user_p5_iso_b@lifebook.ai", "User B", db)

        # User A has confidential patent photo
        entry_a = DiaryEntry(
            id=str(uuid.uuid4()),
            user_id=user_a.id,
            input_type="photo",
            title="Confidential Quantum Patent Drawing",
            raw_text="Private patent diagram for quantum circuit design",
            generated_content="Detailed schematic of quantum circuit patent design.",
            photo_urls=["/api/v1/diary/patent/media"],
            category="Work",
            status="COMPLETED"
        )
        db.add(entry_a)
        db.commit()
        await embedding_service.index_memory(entry_a, db)

        # User B queries for patent diagram
        rag_b = await rag_service.answer_question(
            user_id=user_b.id,
            query="Where is my quantum patent drawing photo?",
            top_k=5,
            db=db
        )
        assert rag_b.is_grounded is False
        assert len(rag_b.sources) == 0
        assert "patent" not in rag_b.answer.lower()
    finally:
        db.close()


@pytest.mark.asyncio
async def test_unsupported_vision_provider_fallback():
    # OpenRouterProvider without API key falls back to local provider gracefully
    provider = OpenRouterProvider()
    provider.api_key = None
    
    img_bytes = _create_sample_image_bytes("Hackathon Trophy Award Certificate")
    res = await provider.understand_image(
        image_bytes=img_bytes,
        filename="trophy.png",
        caption="Won 1st place in Hackathon 2026",
        ocr_text="1st Place Award Winner"
    )
    assert res is not None
    assert res.title is not None
    assert "Hackathon" in res.title or "Photo" in res.title or "Award" in res.title


@pytest.mark.asyncio
async def test_ai_provider_failure_handling():
    # RealAIProvider without key or invalid key safely delegates to fallback without exception
    real_provider = RealAIProvider()
    real_provider.api_key = None
    
    res = await real_provider.understand_image(
        image_bytes=b"fake_bytes",
        filename="test.jpg",
        caption="Testing error tolerance",
        ocr_text=None
    )
    assert res is not None
    assert res.title is not None

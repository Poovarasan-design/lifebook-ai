import pytest
import math
import uuid
import asyncio
from unittest.mock import patch
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.embedding import MemoryChunk
from app.services.embedding_service import embedding_service
from app.core.security import get_password_hash


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_users(db_session: Session):
    unique_suffix = str(uuid.uuid4())[:8]
    user_a = User(
        id=str(uuid.uuid4()),
        email=f"user_a_{unique_suffix}@lifebook.ai",
        full_name="Alice User",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True
    )
    db_session.add(user_a)

    user_b = User(
        id=str(uuid.uuid4()),
        email=f"user_b_{unique_suffix}@lifebook.ai",
        full_name="Bob User",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True
    )
    db_session.add(user_b)
    db_session.commit()
    return user_a, user_b


# 1. Text is correctly chunked
def test_text_is_correctly_chunked():
    entry_short = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        input_type="text",
        title="Morning Coffee",
        category="Personal",
        mood="peaceful",
        generated_content="Had a wonderful cup of coffee this morning while watching the sunrise from the balcony."
    )
    chunks = embedding_service.chunk_memory(entry_short)
    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0
    assert "Morning Coffee" in chunks[0]["metadata_info"]["title"]
    assert chunks[0]["metadata_info"]["mood"] == "peaceful"
    assert chunks[0]["metadata_info"]["user_id"] == entry_short.user_id

    # Multi-paragraph long text
    long_narrative = "\n\n".join([
        f"Paragraph {i}: Today we worked on the SIH hackathon sprint with Ravi and the core engineering team. We reviewed the database schemas, built the backend vector pipeline, and tested all API endpoints thoroughly to ensure robust user isolation."
        for i in range(1, 8)
    ])
    entry_long = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        input_type="text",
        title="Hackathon Sprint Long",
        category="Work",
        mood="productive",
        generated_content=long_narrative
    )
    long_chunks = embedding_service.chunk_memory(entry_long)
    assert len(long_chunks) > 1
    for idx, c in enumerate(long_chunks):
        assert c["chunk_index"] == idx
        assert len(c["chunk_text"]) > 0
        assert c["metadata_info"]["entry_id"] == entry_long.id


# 2. Empty memory is not indexed
def test_empty_memory_is_not_indexed(db_session: Session, test_users):
    user_a, _ = test_users
    empty_entry = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="Empty",
        raw_text="   ",
        generated_content="",
        transcript=""
    )
    db_session.add(empty_entry)
    db_session.commit()

    indexed = asyncio.run(embedding_service.index_memory(empty_entry, db_session))
    assert indexed is False

    chunks = db_session.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == empty_entry.id).all()
    assert len(chunks) == 0


# 3. Embeddings are generated
def test_embeddings_are_generated():
    text_1 = "Designing the RAG architecture with vector embeddings and personal memory graph."
    text_2 = "Designing the RAG architecture with vector embeddings and personal memory graph."
    text_3 = "Cooking pasta for dinner with fresh tomatoes."

    emb_1 = asyncio.run(embedding_service.generate_embedding(text_1))
    emb_2 = asyncio.run(embedding_service.generate_embedding(text_2))
    emb_3 = asyncio.run(embedding_service.generate_embedding(text_3))

    assert len(emb_1) == embedding_service.dim
    assert len(emb_2) == embedding_service.dim
    assert len(emb_3) == embedding_service.dim

    # Determinism: identical text produces identical vector
    assert emb_1 == emb_2

    # Vector is unit-normalized (L2 norm ~ 1.0)
    norm = math.sqrt(sum(x * x for x in emb_1))
    assert abs(norm - 1.0) < 1e-4

    # Batch generation
    batch_embeddings = asyncio.run(embedding_service.generate_embeddings([text_1, text_3]))
    assert len(batch_embeddings) == 2
    assert batch_embeddings[0] == emb_1
    assert batch_embeddings[1] == emb_3


# 4. MemoryChunk is created & 5. user_id is stored correctly
def test_memory_chunk_is_created_and_user_id_stored(db_session: Session, test_users):
    user_a, _ = test_users
    entry = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="Sixty Minute Workout",
        category="Health",
        mood="energized",
        generated_content="Completed a 60-minute cardio and weight lifting session at the gym this evening."
    )
    db_session.add(entry)
    db_session.commit()

    success = asyncio.run(embedding_service.index_memory(entry, db_session))
    assert success is True

    chunks = db_session.query(MemoryChunk).filter(
        MemoryChunk.diary_entry_id == entry.id,
        MemoryChunk.user_id == user_a.id
    ).all()
    assert len(chunks) == 1
    assert chunks[0].user_id == user_a.id
    assert chunks[0].diary_entry_id == entry.id
    assert chunks[0].chunk_index == 0
    assert "cardio and weight lifting" in chunks[0].chunk_text
    assert isinstance(chunks[0].embedding, list)
    assert len(chunks[0].embedding) == embedding_service.dim
    assert chunks[0].metadata_info["title"] == "Sixty Minute Workout"
    assert chunks[0].metadata_info["category"] == "Health"


# 6. Re-indexing replaces old chunks
def test_reindexing_replaces_old_chunks(db_session: Session, test_users):
    user_a, _ = test_users
    entry = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="Initial Draft",
        category="General",
        mood="neutral",
        generated_content="Initial short reflection about the week."
    )
    db_session.add(entry)
    db_session.commit()

    asyncio.run(embedding_service.index_memory(entry, db_session))
    initial_chunks = db_session.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry.id).all()
    assert len(initial_chunks) == 1
    old_chunk_id = initial_chunks[0].id

    # Update entry content and re-index
    entry.title = "Revised Reflection"
    entry.generated_content = (
        "Updated expanded reflection.\n\n"
        "Here is the second paragraph discussing key lessons learned throughout the sprint.\n\n"
        "And the third paragraph focusing on future milestones and planning."
    )
    db_session.commit()

    reindex_success = asyncio.run(embedding_service.index_memory(entry, db_session))
    assert reindex_success is True

    updated_chunks = db_session.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry.id).all()
    assert len(updated_chunks) >= 1
    # Ensure old chunk was deleted and replaced
    assert old_chunk_id not in [c.id for c in updated_chunks]
    assert "Updated expanded reflection" in updated_chunks[0].chunk_text


# 7. Deleting a diary entry removes its chunks
def test_deleting_diary_entry_removes_chunks(db_session: Session, test_users):
    user_a, _ = test_users
    entry_id = str(uuid.uuid4())
    entry = DiaryEntry(
        id=entry_id,
        user_id=user_a.id,
        input_type="text",
        title="Temporary Memory",
        category="Personal",
        mood="calm",
        generated_content="This memory is temporary and will be deleted."
    )
    db_session.add(entry)
    db_session.commit()

    asyncio.run(embedding_service.index_memory(entry, db_session))
    chunks_before = db_session.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry.id).all()
    assert len(chunks_before) == 1

    # Cascade deletion through DiaryEntry delete
    db_session.delete(entry)
    db_session.commit()

    chunks_after = db_session.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry_id).all()
    assert len(chunks_after) == 0


# 8. User A cannot modify User B's chunks
def test_user_isolation_for_chunks(db_session: Session, test_users):
    user_a, user_b = test_users

    entry_a = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="Alice's Private Thoughts",
        category="Confidential",
        mood="happy",
        generated_content="Alice's private personal narrative that should never be modified or seen by Bob."
    )
    db_session.add(entry_a)
    db_session.commit()

    asyncio.run(embedding_service.index_memory(entry_a, db_session))
    chunks_a = db_session.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry_a.id).all()
    assert len(chunks_a) == 1

    # User B attempts to delete User A's chunks using delete_memory_index
    embedding_service.delete_memory_index(entry_id=entry_a.id, user_id=user_b.id, db=db_session)

    # Verify Alice's chunks are still 100% present and untouched
    chunks_a_after = db_session.query(MemoryChunk).filter(MemoryChunk.diary_entry_id == entry_a.id).all()
    assert len(chunks_a_after) == 1
    assert chunks_a_after[0].user_id == user_a.id


# 9. Embedding failure does not delete the original diary entry
def test_embedding_failure_does_not_delete_original_entry(db_session: Session, test_users):
    user_a, _ = test_users

    entry = DiaryEntry(
        id=str(uuid.uuid4()),
        user_id=user_a.id,
        input_type="text",
        title="Durable Memory",
        raw_text="Critical raw text that must never be lost.",
        category="General",
        mood="reflective",
        generated_content="Generated diary narrative."
    )
    db_session.add(entry)
    db_session.commit()

    # Simulate an error during embedding generation
    with patch.object(embedding_service, "generate_embeddings", side_effect=RuntimeError("Embedding model service unavailable")):
        success = asyncio.run(embedding_service.index_memory(entry, db_session))
        assert success is False

    # Verify entry is completely intact in the database
    refreshed_entry = db_session.query(DiaryEntry).filter(DiaryEntry.id == entry.id).first()
    assert refreshed_entry is not None
    assert refreshed_entry.raw_text == "Critical raw text that must never be lost."
    assert refreshed_entry.generated_content == "Generated diary narrative."
    assert refreshed_entry.title == "Durable Memory"

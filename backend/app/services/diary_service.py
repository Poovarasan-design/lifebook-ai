import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.diary import DiaryEntry
from app.models.entity import Entity
from app.models.commitment import Commitment
from app.models.audit import AuditLog
from app.storage.storage_service import storage_service
from app.ai.stt_service import get_stt_provider, get_ai_provider

class DiaryService:
    @staticmethod
    def transition_status(entry: DiaryEntry, status: str, progress: int, message: str, db: Session):
        entry.status = status
        history = list(entry.status_history or [])
        history.append({
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        entry.status_history = history
        db.commit()
        db.refresh(entry)

    @classmethod
    async def create_text_entry(cls, user_id: str, raw_text: str, title: Optional[str], category: Optional[str], mood: Optional[str], db: Session) -> DiaryEntry:
        entry_id = str(uuid.uuid4())
        
        # 1. Save raw text immediately
        raw_path = await storage_service.save_raw_text(user_id, entry_id, raw_text)
        
        # 2. Persist DiaryEntry with status RECEIVED then SAVED
        entry = DiaryEntry(
            id=entry_id,
            user_id=user_id,
            input_type="text",
            raw_text=raw_text,
            title=title or "New Entry",
            category=category or "General",
            mood=mood,
            status="RECEIVED",
            status_history=[{
                "status": "RECEIVED",
                "progress": 10,
                "message": "Raw memory received by gateway",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }]
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        
        cls.transition_status(entry, "SAVED", 25, "Raw text saved to durable storage", db)
        return entry

    @classmethod
    async def process_entry_ai(cls, entry_id: str, db: Optional[Session] = None):
        own_session = False
        if db is None:
            from app.core.database import SessionLocal
            db = SessionLocal()
            own_session = True

        try:
            entry = db.query(DiaryEntry).filter(DiaryEntry.id == entry_id).first()
            if not entry:
                return
                
            ai_provider = get_ai_provider()
            
            # Step 1: Processing by modality
            if entry.input_type == "voice":
                if not entry.transcript:
                    cls.transition_status(entry, "TRANSCRIBING", 40, "Converting voice to text...", db)
                    stt = get_stt_provider()
                    if os.path.exists(entry.media_path):
                        with open(entry.media_path, "rb") as af:
                            audio_bytes = af.read()
                    else:
                        audio_bytes = b""
                    stt_res = await stt.transcribe(audio_bytes, "voice.webm")
                    entry.transcript = stt_res.get("transcript", "")
                    entry.raw_text = entry.transcript
                    db.commit()
                else:
                    cls.transition_status(entry, "TRANSCRIBED", 45, "Speech transcript verified", db)

                cls.transition_status(entry, "EXTRACTING", 60, "Extracting people, places, activities & commitments...", db)
                ai_res = await ai_provider.understand_entry(entry.transcript or entry.raw_text or "")

            elif entry.input_type == "photo":
                cls.transition_status(entry, "EXTRACTING", 50, "Analyzing photo and scanning for readable text...", db)
                from app.services.ocr_service import ocr_service
                img_bytes = b""
                if entry.media_path and os.path.exists(entry.media_path):
                    with open(entry.media_path, "rb") as imf:
                        img_bytes = imf.read()

                # Extract OCR text
                ocr_text = ocr_service.extract_text_from_image(
                    img_bytes,
                    filename=os.path.basename(entry.media_path or "photo.jpg")
                )
                if ocr_text:
                    entry.ocr_text = ocr_text
                    db.commit()

                # Understand image & OCR content
                ai_res = await ai_provider.understand_image(
                    image_bytes=img_bytes,
                    filename=os.path.basename(entry.media_path or "photo.jpg"),
                    caption=entry.raw_text,
                    ocr_text=ocr_text
                )
            else:
                # Text Entry
                cls.transition_status(entry, "EXTRACTING", 60, "Extracting people, places, activities & commitments...", db)
                ai_res = await ai_provider.understand_entry(entry.raw_text or "")
            
            # Save extracted entities
            for p in ai_res.people:
                db.add(Entity(user_id=entry.user_id, diary_entry_id=entry.id, type="person", name=p.name, normalized_name=p.name.lower(), confidence=p.confidence))
            for pl in ai_res.places:
                db.add(Entity(user_id=entry.user_id, diary_entry_id=entry.id, type="place", name=pl.name, normalized_name=pl.name.lower(), confidence=pl.confidence))
            for pr in ai_res.projects:
                db.add(Entity(user_id=entry.user_id, diary_entry_id=entry.id, type="project", name=pr.name, normalized_name=pr.name.lower(), confidence=pr.confidence))
            for ac in ai_res.activities:
                db.add(Entity(user_id=entry.user_id, diary_entry_id=entry.id, type="activity", name=ac.name, normalized_name=ac.name.lower(), confidence=ac.confidence))
            
            # Step 3: Drafted
            cls.transition_status(entry, "DRAFTED", 80, "AI draft generated. Awaiting your review.", db)
            entry.title = ai_res.title
            entry.generated_content = ai_res.diary_draft
            entry.category = ai_res.category
            entry.mood = getattr(ai_res, "mood", None) or entry.mood or "reflective"
            entry.confidence = ai_res.confidence
            entry.disambiguation = ai_res.disambiguation
            
            # Transition to USER_REVIEW
            cls.transition_status(entry, "USER_REVIEW", 85, "Ready for human confirmation", db)
            
        except Exception as ex:
            cls.transition_status(entry, "ENRICHMENT_PENDING", 50, f"AI enrichment delayed: {str(ex)[:100]}", db)
        finally:
            if own_session:
                db.close()

    @classmethod
    async def create_voice_entry(cls, user_id: str, audio_bytes: bytes, filename: str, db: Session, transcript: Optional[str] = None) -> DiaryEntry:
        entry_id = str(uuid.uuid4())
        media_path = await storage_service.save_raw_audio(user_id, entry_id, audio_bytes, filename)
        
        cleaned_transcript = transcript.strip() if transcript else None
        entry = DiaryEntry(
            id=entry_id,
            user_id=user_id,
            input_type="voice",
            media_path=media_path,
            transcript=cleaned_transcript,
            raw_text=cleaned_transcript,
            title="Voice Memory",
            category="General",
            status="RECEIVED",
            status_history=[{
                "status": "RECEIVED",
                "progress": 10,
                "message": "Voice audio received" + (" with verified speech transcript" if cleaned_transcript else ""),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }]
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        
        cls.transition_status(entry, "SAVED", 25, "Raw voice file securely committed to disk", db)
        return entry

    @classmethod
    async def create_photo_entry(cls, user_id: str, image_bytes: bytes, filename: str, caption: Optional[str], db: Session) -> DiaryEntry:
        entry_id = str(uuid.uuid4())
        media_path = await storage_service.save_raw_image(user_id, entry_id, image_bytes, filename)
        
        entry = DiaryEntry(
            id=entry_id,
            user_id=user_id,
            input_type="photo",
            media_path=media_path,
            photo_urls=[f"/api/v1/diary/{entry_id}/media"],
            raw_text=caption or "Photo Memory",
            title=caption or "Visual Memory",
            category="Visual",
            status="RECEIVED",
            status_history=[{
                "status": "RECEIVED",
                "progress": 10,
                "message": "Photo received",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }]
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        
        cls.transition_status(entry, "SAVED", 25, "Raw photo securely committed to disk", db)
        return entry

    @classmethod
    async def confirm_entry(cls, user_id: str, entry_id: str, confirmed_title: Optional[str], confirmed_content: Optional[str], disambiguation_resolution: Optional[Dict[str, str]], db: Session) -> DiaryEntry:
        entry = db.query(DiaryEntry).filter(DiaryEntry.id == entry_id, DiaryEntry.user_id == user_id).first()
        if not entry:
            raise ValueError("Entry not found")

        if confirmed_title:
            entry.title = confirmed_title
        if confirmed_content:
            entry.generated_content = confirmed_content
            
        cls.transition_status(entry, "CONFIRMED", 90, "Memory approved by user", db)
        
        # Sync with Life Graph
        from app.services.life_graph_service import LifeGraphService
        LifeGraphService.sync_entry_to_graph(entry, db)
        cls.transition_status(entry, "GRAPH_UPDATED", 95, "Personal Life Graph connected", db)
        
        # Extract commitments into Commitment model
        from app.services.commitment_service import CommitmentService
        CommitmentService.extract_and_save_commitments(entry, db)

        # Routine Intelligence: detect/sync recurring routines
        from app.services.routine_service import routine_service
        try:
            routine_service.detect_and_sync_user_routines(user_id, db)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Routine sync error: {e}")

        
        # Step: INDEXED (Embeddings & RAG chunks created)
        from app.services.embedding_service import embedding_service
        try:
            indexed = await embedding_service.index_memory(entry, db)
            if indexed:
                cls.transition_status(entry, "INDEXED", 98, "Search indices and vector embeddings prepared", db)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Embedding/indexing failed for entry {entry.id}: {e}")
            # Durability-first: do NOT fail confirmation, preserve user's data

        cls.transition_status(entry, "COMPLETED", 100, "Memory fully archived and connected", db)
        
        # Log audit
        db.add(AuditLog(
            user_id=user_id,
            actor=user_id,
            action="confirm_entry",
            resource=f"DiaryEntry:{entry.id}",
            details={"title": entry.title, "disambiguation": disambiguation_resolution}
        ))
        db.commit()
        db.refresh(entry)
        return entry

    @classmethod
    async def regenerate_entry(
        cls,
        user_id: str,
        entry_id: str,
        tone: Optional[str] = "reflective",
        instructions: Optional[str] = None,
        db: Optional[Session] = None
    ) -> DiaryEntry:
        own_session = False
        if db is None:
            from app.core.database import SessionLocal
            db = SessionLocal()
            own_session = True

        try:
            entry = db.query(DiaryEntry).filter(DiaryEntry.id == entry_id, DiaryEntry.user_id == user_id).first()
            if not entry:
                raise ValueError("Diary entry not found or access denied")

            base_text = entry.raw_text or entry.transcript or entry.generated_content or ""
            if not base_text.strip():
                base_text = entry.title or "Today's thoughts and memories"

            # Get user context
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            user_context = None
            if user:
                user_context = f"User: {user.full_name}. Preferences: {user.preferences or {}}"

            ai_provider = get_ai_provider()
            res = await ai_provider.regenerate_diary(
                text=base_text,
                tone=tone,
                instructions=instructions,
                user_context=user_context
            )

            if res.get("content"):
                entry.generated_content = res.get("content")
            if res.get("title"):
                entry.title = res.get("title")

            current_status = entry.status
            new_status = current_status if current_status in ["COMPLETED", "USER_REVIEW"] else "DRAFTED"
            cls.transition_status(
                entry,
                new_status,
                100 if new_status == "COMPLETED" else 85,
                f"Diary regenerated by AI ({tone or 'reflective'} tone)",
                db
            )

            # Re-index if entry was already completed
            if new_status == "COMPLETED":
                from app.services.embedding_service import embedding_service
                try:
                    await embedding_service.index_memory(entry, db)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Re-indexing failed after regeneration for entry {entry.id}: {e}")

            db.add(AuditLog(
                user_id=user_id,
                actor=user_id,
                action="regenerate_entry",
                resource=f"DiaryEntry:{entry.id}",
                details={"title": entry.title, "tone": tone, "instructions": instructions}
            ))
            db.commit()
            db.refresh(entry)
            return entry
        finally:
            if own_session:
                db.close()

diary_service = DiaryService()

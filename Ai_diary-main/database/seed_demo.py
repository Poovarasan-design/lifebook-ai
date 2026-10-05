import os
import sys
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.config import settings
from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.entity import Entity
from app.models.life_graph import LifeGraphRelationship
from app.models.commitment import Commitment
from app.models.routine import Routine
from app.models.notification import Notification
from app.models.audit import AuditLog

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        email = os.getenv("DEMO_EMAIL", settings.DEMO_EMAIL)
        password = os.getenv("DEMO_PASSWORD", settings.DEMO_PASSWORD)
        name = os.getenv("DEMO_NAME", settings.DEMO_NAME)

        print(f"Seeding demo user: {email} ({name})")
        
        # Check existing
        user = db.query(User).filter(User.email == email).first()
        if user:
            print("Cleaning up old demo records for a fresh seed...")
            db.delete(user)
            db.commit()

        # 1. Create User (Admin & Normal User role enabled for full functionality)
        user = User(
            email=email,
            full_name=name,
            hashed_password=get_password_hash(password),
            role="admin",
            is_active=True,
            preferences={
                "routine_learning": True,
                "location_analysis": True,
                "photo_analysis": True,
                "ai_personalization": True,
                "morning_briefing": True
            }
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 2. Diary Entry 1: Today's Madurai Trip (matches the user's reference image!)
        entry1_id = "entry-madurai-today"
        entry1 = DiaryEntry(
            id=entry1_id,
            user_id=user.id,
            input_type="voice",
            title="A Productive Day in Madurai",
            raw_text="Today I went to Madurai for a customer meeting with Ravi. We discussed the website project and he asked me to send the quotation tomorrow. After the meeting, I had a nice biryani lunch with Kumar at ABC Restaurant. It was a long but fulfilling day. I reached home around 8 PM.",
            transcript="Today I went to Madurai for a customer meeting with Ravi. We discussed the website project and he asked me to send the quotation tomorrow. After the meeting, I had a nice biryani lunch with Kumar at ABC Restaurant. It was a long but fulfilling day. I reached home around 8 PM.",
            generated_content="Today I went to Madurai for a customer meeting with Ravi. We discussed the website project and he asked me to send the quotation tomorrow. After the meeting, I had a nice biryani lunch with Kumar at ABC Restaurant. It was a long but fulfilling day. I reached home around 8 PM.",
            category="Business / Travel",
            mood="fulfilled",
            status="COMPLETED",
            confidence=0.96,
            photo_urls=[
                "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=400&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1577495508048-b635879837f1?w=400&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=400&auto=format&fit=crop&q=80"
            ],
            status_history=[
                {"status": "RECEIVED", "progress": 10, "message": "Voice audio received", "timestamp": "2026-09-10T08:15:00Z"},
                {"status": "SAVED", "progress": 25, "message": "Raw voice file securely committed", "timestamp": "2026-09-10T08:15:02Z"},
                {"status": "TRANSCRIBING", "progress": 40, "message": "Converting speech to text...", "timestamp": "2026-09-10T08:15:05Z"},
                {"status": "EXTRACTING", "progress": 60, "message": "Extracting entities & commitments...", "timestamp": "2026-09-10T08:15:08Z"},
                {"status": "DRAFTED", "progress": 80, "message": "AI narrative polished", "timestamp": "2026-09-10T08:15:10Z"},
                {"status": "USER_REVIEW", "progress": 85, "message": "Draft reviewed by Arun", "timestamp": "2026-09-10T08:16:00Z"},
                {"status": "CONFIRMED", "progress": 90, "message": "Confirmed", "timestamp": "2026-09-10T08:16:15Z"},
                {"status": "GRAPH_UPDATED", "progress": 95, "message": "Life Graph nodes linked", "timestamp": "2026-09-10T08:16:16Z"},
                {"status": "INDEXED", "progress": 98, "message": "Search vector indexed", "timestamp": "2026-09-10T08:16:17Z"},
                {"status": "COMPLETED", "progress": 100, "message": "Fully archived", "timestamp": "2026-09-10T08:16:18Z"}
            ],
            entry_date=datetime.now(timezone.utc)
        )
        db.add(entry1)

        # Entities for Entry 1
        entities_data = [
            ("person", "Ravi"),
            ("person", "Kumar"),
            ("place", "Madurai"),
            ("place", "ABC Restaurant"),
            ("activity", "Customer Meeting"),
            ("activity", "Biryani Lunch"),
            ("activity", "Travel"),
            ("project", "Website Project")
        ]
        for t, n in entities_data:
            db.add(Entity(user_id=user.id, diary_entry_id=entry1_id, type=t, name=n, normalized_name=n.lower(), confidence=0.96))

        # 3. Diary Entry 2: SIH Project Sprint (College)
        entry2_id = "entry-sih-college"
        entry2 = DiaryEntry(
            id=entry2_id,
            user_id=user.id,
            input_type="voice",
            title="SIH Project Sprint at College",
            raw_text="Today I went to college with Ravi. We worked on our SIH project and decided to finish the API next Wednesday.",
            transcript="Today I went to college with Ravi. We worked on our SIH project and decided to finish the API next Wednesday.",
            generated_content="Today I spent time at college collaborating with Ravi on our SIH project. We reviewed our progress and aligned on our next milestone, deciding to finish the core API next Wednesday.",
            category="College / Project",
            mood="motivated",
            status="COMPLETED",
            confidence=0.97,
            entry_date=datetime.now(timezone.utc) - timedelta(days=2)
        )
        db.add(entry2)

        # 4. Diary Entry 3: Historical entry (2 years ago) for "On This Day"
        entry3_id = "entry-marina-beach-past"
        entry3 = DiaryEntry(
            id=entry3_id,
            user_id=user.id,
            input_type="photo",
            title="A Relaxing Evening at Marina Beach",
            raw_text="Watched the sunset with friends. Life feels beautiful in these simple moments.",
            generated_content="Watched the sunset with friends. Life feels beautiful in these simple moments.",
            category="Personal",
            mood="peaceful",
            status="COMPLETED",
            confidence=0.99,
            photo_urls=["https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400&auto=format&fit=crop&q=80"],
            entry_date=datetime(2024, 9, 10, 18, 30, tzinfo=timezone.utc)
        )
        db.add(entry3)

        # 5. Commitments
        c1 = Commitment(
            user_id=user.id,
            diary_entry_id=entry1_id,
            description="Send quotation to Ravi",
            project="Website Project",
            due_date="Due tomorrow",
            status="PENDING",
            priority="high",
            confidence=0.95
        )
        c2 = Commitment(
            user_id=user.id,
            diary_entry_id=entry1_id,
            description="Follow up with Kumar",
            project="Marketing Plan",
            due_date="Due in 3 days",
            status="PENDING",
            priority="medium",
            confidence=0.90
        )
        c3 = Commitment(
            user_id=user.id,
            diary_entry_id=entry2_id,
            description="Finish SIH API",
            project="SIH Project",
            due_date="Next Wednesday",
            status="PENDING",
            priority="high",
            confidence=0.98
        )
        db.add_all([c1, c2, c3])

        # 6. Routines
        r1 = Routine(
            user_id=user.id,
            title="Friday Lunch",
            activity="Lunch at ABC Restaurant",
            location="ABC Restaurant",
            pattern="Friday",
            frequency="weekly",
            details="Sambar Rice",
            occurrence_count=4,
            confidence=0.87,
            is_active=True,
            deviation_prompt="You usually have lunch at ABC Restaurant on Fridays, but today you were travelling to Madurai.",
            deviation_active=True
        )
        db.add(r1)

        # 7. Life Graph Relationships
        graph_data = [
            ("User", "You", "Person", "Ravi", "met"),
            ("User", "You", "Person", "Kumar", "met"),
            ("User", "You", "Place", "Madurai", "visited"),
            ("User", "You", "Place", "ABC Restaurant", "visited"),
            ("User", "You", "Place", "College", "visited"),
            ("Person", "Ravi", "Project", "Website Project", "worked_on"),
            ("Person", "Ravi", "Project", "SIH Project", "worked_on"),
            ("Project", "Website Project", "Commitment", "Send quotation to Ravi", "requires"),
            ("Project", "SIH Project", "Commitment", "Finish SIH API", "requires"),
            ("Person", "Kumar", "Commitment", "Follow up with Kumar", "requires")
        ]
        for st, sn, tt, tn, rel in graph_data:
            db.add(LifeGraphRelationship(
                user_id=user.id,
                diary_entry_id=entry1_id,
                source_type=st,
                source_name=sn,
                target_type=tt,
                target_name=tn,
                relationship_type=rel,
                confidence=0.95
            ))

        # 8. Notifications
        n1 = Notification(
            user_id=user.id,
            title="Commitment Alert",
            message="Send quotation to Ravi is due tomorrow (Website Project).",
            category="commitment"
        )
        n2 = Notification(
            user_id=user.id,
            title="Routine Insight",
            message="You usually have lunch at ABC Restaurant on Fridays, but today you were in Madurai.",
            category="routine"
        )
        n3 = Notification(
            user_id=user.id,
            title="On This Day",
            message="2 years ago: A Relaxing Evening at Marina Beach.",
            category="on_this_day"
        )
        db.add_all([n1, n2, n3])

        # 9. Audit Logs
        db.add(AuditLog(user_id=user.id, actor=user.email, action="demo_seed", resource="FullSeed"))

        db.commit()
        print("Demo seed completed successfully! Account ready:")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  Name: {name}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()

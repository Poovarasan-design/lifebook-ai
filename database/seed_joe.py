import os
import sys
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

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

def seed_joe():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        email = "joe@lifebook.ai"
        password = "JoeLifeBook2026!"
        name = "Jothiram (Joe_Dev)"

        print(f"Creating personalized account for: {name} ({email})")

        # Cleanup previous if exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print("Refreshing existing profile...")
            db.delete(existing)
            db.commit()

        # 1. User
        user = User(
            email=email,
            full_name="Jothiram (Joe)",
            hashed_password=get_password_hash(password),
            role="admin",
            is_active=True,
            preferences={
                "routine_learning": True,
                "location_analysis": True,
                "photo_analysis": True,
                "ai_personalization": True,
                "morning_briefing": True,
                "bio": "CS-Mathematics Student | Full-Stack & AI Developer | Portrait Artist",
                "favorite_foods": ["Biriyani", "Parotta"],
                "friends": ["Poovarasan", "Kisho Varma"]
            }
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 2. Diary Entry 1: Today's College Hackathon Sprint & Parotta Dinner
        entry1_id = "entry-joe-today"
        entry1 = DiaryEntry(
            id=entry1_id,
            user_id=user.id,
            input_type="voice",
            title="SIH Hackathon Sprint & Parotta Dinner with Friends",
            raw_text="Today I went to college with Poovarasan and Kisho Varma. We worked on our SIH hackathon project and finalized the BurnEx AI workout intelligence agent architecture. We decided to finish the pose-estimation module next Wednesday. After college, we had hot parotta and mutton biriyani at our favorite restaurant, and I sketched a new portrait concept.",
            transcript="Today I went to college with Poovarasan and Kisho Varma. We worked on our SIH hackathon project and finalized the BurnEx AI workout intelligence agent architecture. We decided to finish the pose-estimation module next Wednesday. After college, we had hot parotta and mutton biriyani at our favorite restaurant, and I sketched a new portrait concept.",
            generated_content="Today I spent a productive day at college collaborating with Poovarasan and Kisho Varma. We aligned our SIH hackathon strategy and architected the BurnEx AI workout intelligence engine, agreeing to finish the core pose-estimation API next Wednesday. Later in the evening, we celebrated our progress over hot parotta and biriyani while brainstorming ideas for my next portrait art exhibition.",
            category="College / AI Project",
            mood="energized",
            status="COMPLETED",
            confidence=0.98,
            photo_urls=[
                "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=400&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=400&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=400&auto=format&fit=crop&q=80"
            ],
            status_history=[
                {"status": "RECEIVED", "progress": 10, "message": "Voice audio received", "timestamp": "2026-09-10T08:30:00Z"},
                {"status": "SAVED", "progress": 25, "message": "Raw voice safely committed to storage", "timestamp": "2026-09-10T08:30:02Z"},
                {"status": "TRANSCRIBING", "progress": 40, "message": "Converting voice to text...", "timestamp": "2026-09-10T08:30:05Z"},
                {"status": "EXTRACTING", "progress": 60, "message": "Extracted Poovarasan, Kisho Varma, BurnEx AI, Parotta", "timestamp": "2026-09-10T08:30:08Z"},
                {"status": "DRAFTED", "progress": 80, "message": "AI diary draft prepared", "timestamp": "2026-09-10T08:30:10Z"},
                {"status": "USER_REVIEW", "progress": 85, "message": "Reviewed by Joe", "timestamp": "2026-09-10T08:31:00Z"},
                {"status": "CONFIRMED", "progress": 90, "message": "Confirmed", "timestamp": "2026-09-10T08:31:15Z"},
                {"status": "GRAPH_UPDATED", "progress": 95, "message": "Life Graph nodes linked", "timestamp": "2026-09-10T08:31:16Z"},
                {"status": "INDEXED", "progress": 98, "message": "Search vector indexed", "timestamp": "2026-09-10T08:31:17Z"},
                {"status": "COMPLETED", "progress": 100, "message": "Memory fully archived", "timestamp": "2026-09-10T08:31:18Z"}
            ],
            entry_date=datetime.now(timezone.utc)
        )
        db.add(entry1)

        # Entities for Entry 1
        entities_data = [
            ("person", "Poovarasan"),
            ("person", "Kisho Varma"),
            ("place", "College Campus"),
            ("place", "Parotta Corner"),
            ("project", "BurnEx AI"),
            ("project", "SIH Hackathon"),
            ("activity", "AI Architecture Sprint"),
            ("activity", "Portrait Sketching"),
            ("food", "Biriyani"),
            ("food", "Parotta")
        ]
        for t, n in entities_data:
            db.add(Entity(user_id=user.id, diary_entry_id=entry1_id, type=t, name=n, normalized_name=n.lower(), confidence=0.97))

        # 3. Diary Entry 2: Portrait Art Studio & FixMyCollege Web Dev
        entry2_id = "entry-joe-portrait"
        entry2 = DiaryEntry(
            id=entry2_id,
            user_id=user.id,
            input_type="photo",
            title="Creative Flow: Charcoal Portrait Art & Web Dev",
            raw_text="Spent Sunday morning working on a realistic charcoal portrait drawing. Bringing human emotion alive on paper gives me the same creative rush as designing elegant UI and AI architectures. Also pushed fixes for FixMyCollege campus issue manager.",
            generated_content="Spent Sunday morning in my creative zone completing a detailed charcoal portrait. The precision of pencil and shade mirrors the discipline of clean code and AI logic. Later, I refactored the frontend components for the FixMyCollege reporting system.",
            category="Art & Tech",
            mood="creative",
            status="COMPLETED",
            confidence=0.99,
            photo_urls=["https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=400&auto=format&fit=crop&q=80"],
            entry_date=datetime.now(timezone.utc) - timedelta(days=3)
        )
        db.add(entry2)

        # 4. Diary Entry 3: Historical Memory (On This Day - 2 years ago)
        entry3_id = "entry-joe-marina"
        entry3 = DiaryEntry(
            id=entry3_id,
            user_id=user.id,
            input_type="photo",
            title="A Relaxing Evening at Marina Beach",
            raw_text="Watched the sunset at Marina Beach with Poovarasan and Kisho Varma. We discussed future tech startup goals and creative art dreams. Life feels beautiful in these simple moments.",
            generated_content="Watched the sunset at Marina Beach with Poovarasan and Kisho Varma. We discussed future tech startup goals and creative art dreams. Life feels beautiful in these simple moments.",
            category="Personal",
            mood="peaceful",
            status="COMPLETED",
            confidence=0.99,
            photo_urls=["https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400&auto=format&fit=crop&q=80"],
            entry_date=datetime(2024, 9, 10, 18, 0, tzinfo=timezone.utc)
        )
        db.add(entry3)

        # 5. Commitments
        c1 = Commitment(
            user_id=user.id,
            diary_entry_id=entry1_id,
            description="Finish BurnEx pose-estimation module",
            project="BurnEx AI",
            due_date="Next Wednesday",
            status="PENDING",
            priority="high",
            confidence=0.96
        )
        c2 = Commitment(
            user_id=user.id,
            diary_entry_id=entry1_id,
            description="Discuss SIH hackathon architecture with Poovarasan & Kisho",
            project="SIH Hackathon",
            due_date="Due tomorrow",
            status="PENDING",
            priority="high",
            confidence=0.94
        )
        c3 = Commitment(
            user_id=user.id,
            diary_entry_id=entry2_id,
            description="Solve 2 Dynamic Programming problems on LeetCode",
            project="Placement Prep",
            due_date="Due in 2 days",
            status="PENDING",
            priority="medium",
            confidence=0.90
        )
        c4 = Commitment(
            user_id=user.id,
            diary_entry_id=entry2_id,
            description="Upload charcoal portrait drawing timelapse",
            project="Art Portfolio",
            due_date="Due Sunday",
            status="PENDING",
            priority="medium",
            confidence=0.92
        )
        db.add_all([c1, c2, c3, c4])

        # 6. Routines
        r1 = Routine(
            user_id=user.id,
            title="Friday Biriyani & Parotta Dinner",
            activity="Dinner with Poovarasan & Kisho Varma",
            location="Parotta Corner",
            pattern="Friday",
            frequency="weekly",
            details="Hot Parotta & Mutton Biriyani",
            occurrence_count=5,
            confidence=0.94,
            is_active=True,
            deviation_prompt="You usually have Parotta & Biriyani dinner on Fridays with Poovarasan and Kisho Varma, but today you were working late on hackathon code.",
            deviation_active=True
        )
        r2 = Routine(
            user_id=user.id,
            title="Sunday Portrait Sketching",
            activity="Portrait Drawing & Charcoal Studies",
            location="Art Studio Desk",
            pattern="Sunday",
            frequency="weekly",
            details="Portrait art & visual aesthetics",
            occurrence_count=6,
            confidence=0.91,
            is_active=True,
            deviation_active=False
        )
        db.add_all([r1, r2])

        # 7. Life Graph Relationships
        graph_links = [
            ("User", "Joe", "Person", "Poovarasan", "met"),
            ("User", "Joe", "Person", "Kisho Varma", "met"),
            ("User", "Joe", "Place", "College Campus", "visited"),
            ("User", "Joe", "Place", "Parotta Corner", "visited"),
            ("User", "Joe", "Project", "BurnEx AI", "worked_on"),
            ("User", "Joe", "Project", "SIH Hackathon", "worked_on"),
            ("User", "Joe", "Project", "Portrait Art", "creates"),
            ("Person", "Poovarasan", "Project", "SIH Hackathon", "worked_on"),
            ("Person", "Kisho Varma", "Project", "BurnEx AI", "worked_on"),
            ("Project", "BurnEx AI", "Commitment", "Finish BurnEx pose-estimation module", "requires"),
            ("Project", "SIH Hackathon", "Commitment", "Discuss SIH hackathon architecture with Poovarasan & Kisho", "requires")
        ]
        for st, sn, tt, tn, rel in graph_links:
            db.add(LifeGraphRelationship(
                user_id=user.id,
                diary_entry_id=entry1_id,
                source_type=st,
                source_name=sn,
                target_type=tt,
                target_name=tn,
                relationship_type=rel,
                confidence=0.96
            ))

        # 8. Notifications
        n1 = Notification(
            user_id=user.id,
            title="SIH Hackathon Sprint",
            message="Meeting with Poovarasan and Kisho Varma scheduled for tomorrow.",
            category="commitment"
        )
        n2 = Notification(
            user_id=user.id,
            title="BurnEx AI Milestone",
            message="Finish BurnEx pose-estimation module due next Wednesday.",
            category="commitment"
        )
        n3 = Notification(
            user_id=user.id,
            title="Routine Reminder",
            message="Friday Parotta & Biriyani dinner with friends.",
            category="routine"
        )
        db.add_all([n1, n2, n3])

        # 9. Audit Log
        db.add(AuditLog(
            user_id=user.id,
            actor=user.email,
            action="personalized_seed",
            resource="JoeProfile"
        ))

        db.commit()
        print(f"Personalized account successfully initialized for {name}!")
        print(f"  Login Email:    {email}")
        print(f"  Login Password: {password}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding personalized account: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_joe()

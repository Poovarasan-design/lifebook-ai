import pytest
from app.core.database import SessionLocal, Base, engine, init_db
from app.core.security import get_password_hash
from app.models.user import User

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "jothiram@lifebook.ai").first()
        if not user:
            user = User(
                email="jothiram@lifebook.ai",
                full_name="Jothiram",
                hashed_password=get_password_hash("LifeBook2026!"),
                role="admin",
                is_active=True
            )
            db.add(user)
            db.commit()
    finally:
        db.close()

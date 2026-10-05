from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.commitment import Commitment
from app.models.routine import Routine
from app.schemas.auth import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)

@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.full_name:
        current_user.full_name = payload.full_name
    if payload.preferences is not None:
        p = dict(current_user.preferences or {})
        p.update(payload.preferences)
        current_user.preferences = p
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)

@router.post("/me/export")
def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entries = db.query(DiaryEntry).filter(DiaryEntry.user_id == current_user.id).all()
    commitments = db.query(Commitment).filter(Commitment.user_id == current_user.id).all()
    routines = db.query(Routine).filter(Routine.user_id == current_user.id).all()
    
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "preferences": current_user.preferences
        },
        "diary_entries": [
            {
                "id": e.id,
                "title": e.title,
                "category": e.category,
                "generated_content": e.generated_content,
                "raw_text": e.raw_text,
                "created_at": e.created_at.isoformat()
            }
            for e in entries
        ],
        "commitments": [
            {
                "id": c.id,
                "description": c.description,
                "due_date": c.due_date,
                "status": c.status
            }
            for c in commitments
        ],
        "routines": [
            {
                "id": r.id,
                "title": r.title,
                "pattern": r.pattern,
                "frequency": r.frequency
            }
            for r in routines
        ]
    }

@router.delete("/me")
def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.delete(current_user)
    db.commit()
    return {"message": "User account and all associated data permanently deleted"}

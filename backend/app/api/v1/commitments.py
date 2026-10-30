from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.commitment import Commitment
from app.schemas.commitment import CommitmentOut, CommitmentCreate, CommitmentUpdate
from app.services.commitment_service import CommitmentService

router = APIRouter(prefix="/commitments", tags=["commitments"])

@router.get("", response_model=List[CommitmentOut])
def get_commitments(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items = CommitmentService.get_user_commitments(current_user.id, status, db)
    return [CommitmentOut.model_validate(c) for c in items]

@router.post("", response_model=CommitmentOut)
def create_commitment(
    payload: CommitmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    c = Commitment(
        user_id=current_user.id,
        description=payload.description,
        project=payload.project,
        due_date=payload.due_date,
        priority=payload.priority or "high",
        status="PENDING",
        confidence=1.0
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return CommitmentOut.model_validate(c)

@router.post("/{commitment_id}/complete", response_model=CommitmentOut)
def complete_commitment(
    commitment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    c = db.query(Commitment).filter(Commitment.id == commitment_id, Commitment.user_id == current_user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Commitment not found")
    c.status = "COMPLETED"
    db.commit()
    db.refresh(c)
    return CommitmentOut.model_validate(c)

@router.post("/{commitment_id}/reschedule", response_model=CommitmentOut)
def reschedule_commitment(
    commitment_id: str,
    new_due_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    c = db.query(Commitment).filter(Commitment.id == commitment_id, Commitment.user_id == current_user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Commitment not found")
    c.due_date = new_due_date
    c.status = "RESCHEDULED"
    db.commit()
    db.refresh(c)
    return CommitmentOut.model_validate(c)

@router.post("/{commitment_id}/dismiss", response_model=CommitmentOut)
def dismiss_commitment(
    commitment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    c = db.query(Commitment).filter(Commitment.id == commitment_id, Commitment.user_id == current_user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Commitment not found")
    c.status = "DISMISSED"
    db.commit()
    db.refresh(c)
    return CommitmentOut.model_validate(c)

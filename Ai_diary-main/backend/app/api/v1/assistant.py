from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.schemas.assistant import TodayAssistantResponse
from app.services.memory_intelligence_service import memory_intelligence_service

router = APIRouter(prefix="/assistant", tags=["assistant"])

@router.get("/today", response_model=TodayAssistantResponse)
def get_today_assistant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the proactive Today Assistant briefing strictly scoped to the authenticated user.
    Surfaces: Needs Attention (High priority overdue/due-today/stale), Upcoming, Routine Changes, and Reminders.
    """
    res = memory_intelligence_service.get_today_assistant(current_user.id, db)
    return TodayAssistantResponse(**res)

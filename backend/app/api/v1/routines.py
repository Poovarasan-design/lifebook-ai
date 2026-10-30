from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.entity import Entity
from app.models.commitment import Commitment
from app.schemas.routine import RoutineOut, RoutineDeviationAction
from app.services.routine_service import RoutineService

router = APIRouter(prefix="/routines", tags=["routines"])

@router.get("", response_model=List[RoutineOut])
def get_routines(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items = RoutineService.get_user_routines(current_user.id, db)
    return [RoutineOut.model_validate(r) for r in items]

@router.get("/insights")
def get_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.memory_intelligence_service import memory_intelligence_service

    # Check deviations to refresh routine statuses
    memory_intelligence_service.check_routine_deviations(current_user.id, db)

    # 1. User routines
    routines = RoutineService.get_user_routines(current_user.id, db)
    routines_out = [RoutineOut.model_validate(r).model_dump() for r in routines]

    # 2. Entries & Mood stats
    entries = db.query(DiaryEntry).filter(DiaryEntry.user_id == current_user.id).order_by(DiaryEntry.entry_date.desc()).all()
    mood_counts = {}
    category_counts = {}
    for e in entries:
        if e.mood:
            mood_counts[e.mood] = mood_counts.get(e.mood, 0) + 1
        if e.category:
            category_counts[e.category] = category_counts.get(e.category, 0) + 1

    # 3. People & Places frequency
    entities = db.query(Entity).filter(Entity.user_id == current_user.id).all()
    people_map = {}
    places_map = {}
    for ent in entities:
        if ent.type == "person":
            people_map[ent.name] = people_map.get(ent.name, 0) + 1
        elif ent.type == "place":
            places_map[ent.name] = places_map.get(ent.name, 0) + 1

    top_people = sorted([{"name": k, "count": v} for k, v in people_map.items()], key=lambda x: x["count"], reverse=True)[:5]
    top_places = sorted([{"name": k, "count": v} for k, v in places_map.items()], key=lambda x: x["count"], reverse=True)[:5]

    # 4. Commitments overview
    commitments = db.query(Commitment).filter(Commitment.user_id == current_user.id).all()
    pending_comm = sum(1 for c in commitments if c.status == "PENDING")
    completed_comm = sum(1 for c in commitments if c.status == "COMPLETED")

    # 5. Smart AI life observations from memory intelligence
    smart_data = memory_intelligence_service.get_smart_insights(current_user.id, db)
    observations = smart_data.get("ai_observations", [])

    return {
        "routines": routines_out,
        "total_memories": len(entries),
        "mood_distribution": mood_counts,
        "category_distribution": category_counts,
        "top_people": top_people,
        "top_places": top_places,
        "commitments_summary": {
            "pending": pending_comm,
            "completed": completed_comm,
            "total": len(commitments),
            "urgent_items": smart_data.get("commitments_summary", {}).get("urgent_items", [])
        },
        "routine_deviations": smart_data.get("routine_deviations", []),
        "ai_observations": observations
    }


@router.post("/{routine_id}/action", response_model=RoutineOut)
def handle_deviation(
    routine_id: str,
    payload: RoutineDeviationAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        updated = RoutineService.handle_deviation_action(routine_id, current_user.id, payload.action, payload.note, db)
        return RoutineOut.model_validate(updated)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


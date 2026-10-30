from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.schemas.graph import LifeGraphOut, EntityHistoryOut
from app.services.life_graph_service import LifeGraphService

router = APIRouter(prefix="/life-graph", tags=["life-graph"])

@router.get("", response_model=LifeGraphOut)
def get_life_graph(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns full deduplicated Life Graph for the authenticated user.
    """
    return LifeGraphService.get_user_graph(current_user.id, db)

@router.get("/entities")
def get_life_graph_entities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns summarized entity collections (people, places, projects).
    """
    return LifeGraphService.get_user_entities(current_user.id, db)

@router.get("/person/{name}/history", response_model=EntityHistoryOut)
def get_person_history(
    name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns chronological timeline, connected projects, places, and commitments for a person.
    """
    return LifeGraphService.get_person_history(current_user.id, name, db)

@router.get("/project/{name}/history", response_model=EntityHistoryOut)
def get_project_history(
    name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns chronological timeline, collaborators, and commitments for a project.
    """
    return LifeGraphService.get_project_history(current_user.id, name, db)

@router.get("/place/{name}/history", response_model=EntityHistoryOut)
def get_place_history(
    name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns chronological timeline, activities, photos, and co-visitors for a place.
    """
    return LifeGraphService.get_place_history(current_user.id, name, db)

@router.get("/entity-history", response_model=EntityHistoryOut)
def get_entity_history(
    type: str = Query(..., description="Entity type: person, place, project, activity"),
    name: str = Query(..., description="Entity name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unified endpoint to fetch timeline history for any entity.
    """
    return LifeGraphService.get_entity_history(current_user.id, type, name, db)

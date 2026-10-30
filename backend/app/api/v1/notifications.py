from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("")
def list_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Sync reminders on fetch
    notification_service.sync_reminders(current_user.id, db)
    return notification_service.get_user_notifications(current_user.id, db, unread_only=unread_only)

@router.post("/{notification_id}/read")
def mark_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = notification_service.mark_as_read(notification_id, current_user.id, db)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read", "id": notification_id}

@router.post("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = notification_service.mark_all_as_read(current_user.id, db)
    return {"message": "All notifications marked as read", "count": count}

@router.delete("/{notification_id}")
def dismiss_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = notification_service.dismiss_notification(notification_id, current_user.id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification dismissed", "id": notification_id}

@router.patch("/preferences")
def update_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current = dict(current_user.preferences or {})
    current.update(preferences)
    current_user.preferences = current
    db.commit()
    return {"message": "Preferences updated", "preferences": current_user.preferences}

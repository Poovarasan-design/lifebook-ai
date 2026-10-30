from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.commitment import Commitment

class NotificationService:
    @staticmethod
    def get_user_notifications(user_id: str, db: Session, unread_only: bool = False) -> List[Notification]:
        q = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            q = q.filter(Notification.is_read == False)
        return q.order_by(Notification.created_at.desc()).all()

    @staticmethod
    def create_notification(
        user_id: str,
        title: str,
        message: str,
        category: str = "commitment",
        db: Session = None,
        metadata_json: Optional[Dict[str, Any]] = None
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            metadata_json=metadata_json or {}
        )
        if db is not None:
            db.add(notif)
            db.commit()
            db.refresh(notif)
        return notif

    @staticmethod
    def mark_as_read(notification_id: str, user_id: str, db: Session) -> Optional[Notification]:
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if notif:
            notif.is_read = True
            db.commit()
            db.refresh(notif)
        return notif

    @staticmethod
    def mark_all_as_read(user_id: str, db: Session) -> int:
        updated = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True}, synchronize_session=False)
        db.commit()
        return updated

    @staticmethod
    def dismiss_notification(notification_id: str, user_id: str, db: Session) -> bool:
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if notif:
            db.delete(notif)
            db.commit()
            return True
        return False

    @staticmethod
    def sync_reminders(user_id: str, db: Session) -> List[Notification]:
        """
        Manages the complete reminder lifecycle for the authenticated user:
        pending -> upcoming -> due -> overdue -> completed/dismissed.

        Rules:
        - Prevents duplicate reminders for the same commitment and lifecycle state.
        - Completed/dismissed commitments never generate reminders.
        - Unread notifications for completed/dismissed commitments are marked read.
        - High priority for overdue / due today; medium priority for upcoming / stale.
        """
        now = datetime.now(timezone.utc)
        
        # 1. Fetch user's active commitments
        commitments = db.query(Commitment).filter(
            Commitment.user_id == user_id
        ).all()

        active_commitments = [c for c in commitments if c.status in ["PENDING", "RESCHEDULED"]]
        inactive_commitment_ids = {c.id for c in commitments if c.status in ["COMPLETED", "DISMISSED"]}

        # 2. Mark existing unread notifications for inactive/completed commitments as read
        existing_notifs = db.query(Notification).filter(
            Notification.user_id == user_id
        ).all()

        for notif in existing_notifs:
            meta = notif.metadata_json or {}
            c_id = meta.get("commitment_id")
            if c_id and c_id in inactive_commitment_ids and not notif.is_read:
                notif.is_read = True

        db.commit()

        # Build lookup of existing reminder notifications to prevent duplicates
        existing_reminder_keys = set()
        for notif in existing_notifs:
            meta = notif.metadata_json or {}
            c_id = meta.get("commitment_id")
            stage = meta.get("reminder_stage")
            if c_id and stage:
                existing_reminder_keys.add((c_id, stage))

        new_notifications: List[Notification] = []

        for c in active_commitments:
            due_dt = c.resolved_due_date
            if due_dt and due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)

            created_dt = c.created_at
            if created_dt and created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)

            stage = None
            priority = "medium"
            title = f"Reminder: {c.description[:50]}"
            message = ""

            if due_dt:
                diff_seconds = (due_dt - now).total_seconds()
                if diff_seconds < 0:
                    # Past deadline -> Overdue
                    stage = "overdue"
                    priority = "high"
                    title = f"Overdue: {c.description[:50]}"
                    message = f"Action item '{c.description}' was due on {due_dt.strftime('%B %d')}."
                elif diff_seconds <= 86400 * 1.5:
                    # Due today or tomorrow -> Due Soon
                    stage = "due"
                    priority = "high"
                    title = f"Due Soon: {c.description[:50]}"
                    message = f"Action item '{c.description}' is due {c.due_date or 'today'}."
                elif diff_seconds <= 86400 * 7:
                    # Upcoming within 7 days
                    stage = "upcoming"
                    priority = "medium"
                    title = f"Upcoming: {c.description[:50]}"
                    message = f"Upcoming commitment '{c.description}' (Due: {c.due_date or due_dt.strftime('%B %d')})."
            else:
                # No explicit resolved date, check if stale (>= 3 days old)
                if created_dt and (now - created_dt).days >= 3:
                    stage = "stale"
                    priority = "medium"
                    title = f"Pending Action: {c.description[:50]}"
                    message = f"Commitment recorded {(now - created_dt).days} days ago is still pending: '{c.description}'."
                else:
                    stage = "pending"
                    priority = "medium"

            # Check if this stage reminder was already generated
            if stage and (c.id, stage) not in existing_reminder_keys:
                notif = Notification(
                    user_id=user_id,
                    title=title,
                    message=message or f"Reminder for {c.description}",
                    category="commitment",
                    channel="in_app",
                    is_read=False,
                    metadata_json={
                        "commitment_id": c.id,
                        "reminder_stage": stage,
                        "priority": priority,
                        "due_date": c.due_date,
                        "project": c.project
                    }
                )
                db.add(notif)
                new_notifications.append(notif)
                existing_reminder_keys.add((c.id, stage))

        if new_notifications:
            db.commit()

        return new_notifications

notification_service = NotificationService()

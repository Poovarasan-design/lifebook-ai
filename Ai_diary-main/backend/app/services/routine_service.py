from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.routine import Routine

class RoutineService:
    @staticmethod
    def get_user_routines(user_id: str, db: Session) -> List[Routine]:
        return db.query(Routine).filter(Routine.user_id == user_id, Routine.is_active == True).all()

    @staticmethod
    def detect_and_sync_user_routines(user_id: str, db: Session, min_occurrences: int = 2) -> List[Routine]:
        from app.services.memory_intelligence_service import memory_intelligence_service
        return memory_intelligence_service.detect_user_routines(user_id, db, min_occurrences)

    @staticmethod
    def check_deviations(user_id: str, db: Session) -> List[Routine]:
        from app.services.memory_intelligence_service import memory_intelligence_service
        return memory_intelligence_service.check_routine_deviations(user_id, db)

    @staticmethod
    def handle_deviation_action(routine_id: str, user_id: str, action: str, note: Optional[str], db: Session) -> Routine:
        routine = db.query(Routine).filter(Routine.id == routine_id, Routine.user_id == user_id).first()
        if not routine:
            raise ValueError("Routine not found")

        if action == "disable_routine":
            routine.is_active = False
            routine.disabled_reason = "User requested don't treat this as a routine"
        elif action == "skipped":
            routine.deviation_active = False
        elif action == "changed":
            routine.deviation_active = False
            if note:
                routine.details = note

        db.commit()
        db.refresh(routine)
        return routine

routine_service = RoutineService()


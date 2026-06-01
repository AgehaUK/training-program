from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.failure_mode import FailureMode


class FailureModeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> List[FailureMode]:
        return self.db.query(FailureMode).order_by(FailureMode.id).all()

    def find_by_name(self, name: str) -> Optional[FailureMode]:
        return self.db.query(FailureMode).filter(FailureMode.name == name).first()

    def find_or_create_by_name(self, name: str) -> FailureMode:
        mode = self.find_by_name(name)
        if mode is None:
            mode = FailureMode(name=name)
            self.db.add(mode)
            self.db.commit()
            self.db.refresh(mode)
        return mode

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class FailureReport(Base):
    __tablename__ = "failure_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_text = Column(Text, nullable=False)
    occurred_at = Column(Date, nullable=False)
    equipment_name = Column(String(200), nullable=False)
    symptom = Column(Text, nullable=False)
    cause = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)
    cost = Column(Integer, nullable=True)
    downtime_hours = Column(Float, nullable=True)
    failure_mode_id = Column(Integer, ForeignKey("failure_modes.id"), nullable=True)
    source = Column(String(20), nullable=False, default="manual")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    failure_mode = relationship("FailureMode", back_populates="reports")

    __table_args__ = (
        Index("idx_failure_reports_occurred_at", "occurred_at"),
        Index("idx_failure_reports_failure_mode_id", "failure_mode_id"),
        Index("idx_failure_reports_equipment_name", "equipment_name"),
    )

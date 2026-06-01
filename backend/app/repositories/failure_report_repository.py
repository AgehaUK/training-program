"""
FailureReport リポジトリ

Data Access Layer: failure_reports テーブルへのアクセス
"""
from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.failure_mode import FailureMode
from app.models.failure_report import FailureReport


class FailureReportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search(
        self,
        keyword: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        failure_mode_id: Optional[int] = None,
        cost_min: Optional[int] = None,
        cost_max: Optional[int] = None,
        sort: str = "occurred_at",
        order: str = "desc",
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[FailureReport], int]:
        q = self.db.query(FailureReport)

        if keyword:
            pattern = f"%{keyword}%"
            q = q.filter(
                or_(
                    FailureReport.equipment_name.like(pattern),
                    FailureReport.symptom.like(pattern),
                    FailureReport.cause.like(pattern),
                    FailureReport.action_taken.like(pattern),
                )
            )

        if from_date:
            q = q.filter(FailureReport.occurred_at >= from_date)
        if to_date:
            q = q.filter(FailureReport.occurred_at <= to_date)
        if failure_mode_id is not None:
            q = q.filter(FailureReport.failure_mode_id == failure_mode_id)
        if cost_min is not None:
            q = q.filter(FailureReport.cost >= cost_min)
        if cost_max is not None:
            q = q.filter(FailureReport.cost <= cost_max)

        total = q.count()

        sort_col = getattr(FailureReport, sort, FailureReport.occurred_at)
        if order == "asc":
            q = q.order_by(sort_col.asc())
        else:
            q = q.order_by(sort_col.desc())

        offset = (page - 1) * per_page
        reports = q.offset(offset).limit(per_page).all()
        return reports, total

    def search_by_ids(
        self,
        ids: List[int],
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        failure_mode_id: Optional[int] = None,
        cost_min: Optional[int] = None,
        cost_max: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[FailureReport], int]:
        """FAISSが返したIDリストを元にDBから取得（類似度順を維持）"""
        if not ids:
            return [], 0
        q = self.db.query(FailureReport).filter(FailureReport.id.in_(ids))
        if from_date:
            q = q.filter(FailureReport.occurred_at >= from_date)
        if to_date:
            q = q.filter(FailureReport.occurred_at <= to_date)
        if failure_mode_id is not None:
            q = q.filter(FailureReport.failure_mode_id == failure_mode_id)
        if cost_min is not None:
            q = q.filter(FailureReport.cost >= cost_min)
        if cost_max is not None:
            q = q.filter(FailureReport.cost <= cost_max)

        all_reports = q.all()
        # FAISSの類似度順（idsの順番）を維持
        id_order = {rid: i for i, rid in enumerate(ids)}
        all_reports.sort(key=lambda r: id_order.get(r.id, len(ids)))

        total = len(all_reports)
        offset = (page - 1) * per_page
        return all_reports[offset: offset + per_page], total

    def find_by_id(self, report_id: int) -> Optional[FailureReport]:
        return self.db.query(FailureReport).filter(FailureReport.id == report_id).first()

    def create(
        self,
        original_text: str,
        occurred_at: date,
        equipment_name: str,
        symptom: str,
        cause: Optional[str] = None,
        action_taken: Optional[str] = None,
        cost: Optional[int] = None,
        downtime_hours: Optional[float] = None,
        failure_mode_id: Optional[int] = None,
        source: str = "manual",
    ) -> FailureReport:
        report = FailureReport(
            original_text=original_text,
            occurred_at=occurred_at,
            equipment_name=equipment_name,
            symptom=symptom,
            cause=cause,
            action_taken=action_taken,
            cost=cost,
            downtime_hours=downtime_hours,
            failure_mode_id=failure_mode_id,
            source=source,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

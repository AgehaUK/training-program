"""
ダッシュボード リポジトリ

Data Access Layer: ダッシュボード集計クエリ
"""
from collections import defaultdict
from datetime import date
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.failure_report import FailureReport


class DashboardRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _base_query(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        equipment_name: Optional[str] = None,
        failure_mode_id: Optional[int] = None,
    ):
        q = self.db.query(FailureReport)
        if from_date:
            q = q.filter(FailureReport.occurred_at >= from_date)
        if to_date:
            q = q.filter(FailureReport.occurred_at <= to_date)
        if equipment_name:
            q = q.filter(FailureReport.equipment_name == equipment_name)
        if failure_mode_id is not None:
            q = q.filter(FailureReport.failure_mode_id == failure_mode_id)
        return q

    def get_summary(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        equipment_name: Optional[str] = None,
        failure_mode_id: Optional[int] = None,
    ) -> Dict:
        reports = self._base_query(from_date, to_date, equipment_name, failure_mode_id).all()
        total_count = len(reports)
        total_cost = sum(r.cost for r in reports if r.cost is not None)
        downtime_list = [r.downtime_hours for r in reports if r.downtime_hours is not None]
        avg_downtime = round(sum(downtime_list) / len(downtime_list), 2) if downtime_list else 0.0
        return {
            "total_count": total_count,
            "total_cost": total_cost,
            "avg_downtime_hours": avg_downtime,
        }

    def get_failure_mode_breakdown(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        equipment_name: Optional[str] = None,
        failure_mode_id: Optional[int] = None,
    ) -> List[Dict]:
        reports = self._base_query(from_date, to_date, equipment_name, failure_mode_id).all()
        counts: Dict[str, int] = defaultdict(int)
        for r in reports:
            mode_name = r.failure_mode.name if r.failure_mode else "不明"
            counts[mode_name] += 1
        return [
            {"failure_mode": name, "count": count}
            for name, count in sorted(counts.items(), key=lambda x: -x[1])
        ]

    def get_monthly_trend(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        equipment_name: Optional[str] = None,
        failure_mode_id: Optional[int] = None,
    ) -> List[Dict]:
        reports = self._base_query(from_date, to_date, equipment_name, failure_mode_id).all()
        counts: Dict[str, int] = defaultdict(int)
        for r in reports:
            month = str(r.occurred_at)[:7]
            counts[month] += 1
        return [{"month": month, "count": count} for month, count in sorted(counts.items())]

    def get_cost_top10(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        equipment_name: Optional[str] = None,
        failure_mode_id: Optional[int] = None,
    ) -> List[Dict]:
        reports = self._base_query(from_date, to_date, equipment_name, failure_mode_id).all()
        totals: Dict[str, int] = defaultdict(int)
        for r in reports:
            if r.cost is not None:
                totals[r.equipment_name] += r.cost
        sorted_items = sorted(totals.items(), key=lambda x: -x[1])[:10]
        return [{"equipment_name": name, "total_cost": total} for name, total in sorted_items]

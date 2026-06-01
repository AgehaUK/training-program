"""
Slice 3: ダッシュボード API のテスト
"""
from datetime import date

from app.repositories.failure_mode_repository import FailureModeRepository
from app.repositories.failure_report_repository import FailureReportRepository


def _seed_reports(db_session):
    mode_repo = FailureModeRepository(db_session)
    mode1 = mode_repo.find_or_create_by_name("電気系故障")
    mode2 = mode_repo.find_or_create_by_name("機械系故障")
    repo = FailureReportRepository(db_session)
    repo.create(original_text="テスト1", occurred_at=date(2025, 1, 10),
                equipment_name="設備A", symptom="停止", cost=50000, downtime_hours=2.0, failure_mode_id=mode1.id)
    repo.create(original_text="テスト2", occurred_at=date(2025, 1, 20),
                equipment_name="設備B", symptom="異音", cost=120000, downtime_hours=4.0, failure_mode_id=mode1.id)
    repo.create(original_text="テスト3", occurred_at=date(2025, 2, 5),
                equipment_name="設備A", symptom="漏れ", cost=30000, downtime_hours=1.0, failure_mode_id=mode2.id)
    repo.create(original_text="コストなし", occurred_at=date(2025, 3, 1),
                equipment_name="設備C", symptom="エラー", failure_mode_id=mode2.id)


class TestDashboardSummaryAPI:
    def test_summary_requires_auth(self, api_client):
        assert api_client.get("/api/dashboard/summary").status_code == 401

    def test_summary_correct_total_count(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = api_client.get("/api/dashboard/summary", headers=admin_headers).json()["data"]
        assert data["total_count"] == 4

    def test_summary_correct_total_cost(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = api_client.get("/api/dashboard/summary", headers=admin_headers).json()["data"]
        assert data["total_cost"] == 200000

    def test_summary_correct_avg_downtime(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = api_client.get("/api/dashboard/summary", headers=admin_headers).json()["data"]
        assert data["avg_downtime_hours"] == round((2.0 + 4.0 + 1.0) / 3, 2)

    def test_summary_empty_db_returns_zeros(self, api_client, admin_headers):
        data = api_client.get("/api/dashboard/summary", headers=admin_headers).json()["data"]
        assert data["total_count"] == 0
        assert data["total_cost"] == 0

    def test_summary_with_date_filter(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = api_client.get("/api/dashboard/summary?from_date=2025-02-01", headers=admin_headers).json()["data"]
        assert data["total_count"] == 2


class TestDashboardFailureModesAPI:
    def test_failure_modes_returns_list(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        res = api_client.get("/api/dashboard/failure-modes", headers=admin_headers)
        assert res.status_code == 200
        assert isinstance(res.json()["data"], list)

    def test_failure_modes_counts_correct(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = {d["failure_mode"]: d["count"]
                for d in api_client.get("/api/dashboard/failure-modes", headers=admin_headers).json()["data"]}
        assert data["電気系故障"] == 2
        assert data["機械系故障"] == 2


class TestDashboardTrendAPI:
    def test_trend_returns_monthly_data(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = api_client.get("/api/dashboard/trend", headers=admin_headers).json()["data"]
        assert len(data) >= 2

    def test_trend_counts_per_month(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        monthly = {d["month"]: d["count"]
                   for d in api_client.get("/api/dashboard/trend", headers=admin_headers).json()["data"]}
        assert monthly.get("2025-01") == 2
        assert monthly.get("2025-02") == 1


class TestDashboardCostTop10API:
    def test_cost_top10_sorted_descending(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = api_client.get("/api/dashboard/cost-top10", headers=admin_headers).json()["data"]
        costs = [d["total_cost"] for d in data]
        assert costs == sorted(costs, reverse=True)

    def test_cost_top10_excludes_null_cost(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        names = [d["equipment_name"]
                 for d in api_client.get("/api/dashboard/cost-top10", headers=admin_headers).json()["data"]]
        assert "設備C" not in names

    def test_cost_top10_aggregates_by_equipment(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = {d["equipment_name"]: d["total_cost"]
                for d in api_client.get("/api/dashboard/cost-top10", headers=admin_headers).json()["data"]}
        assert data["設備A"] == 80000

"""
Slice 5: GET /api/reports（検索一覧）と GET /api/reports/:id（詳細）のテスト

キーワード検索は FAISS をモックして DB フィルタリング層をテストする。
"""
from datetime import date
from unittest.mock import patch

from app.repositories.failure_mode_repository import FailureModeRepository
from app.repositories.failure_report_repository import FailureReportRepository


def _seed_reports(db_session):
    mode_repo = FailureModeRepository(db_session)
    mode1 = mode_repo.find_or_create_by_name("電気系故障")
    mode2 = mode_repo.find_or_create_by_name("機械系故障")
    repo = FailureReportRepository(db_session)
    r1 = repo.create(
        original_text="温度センサー故障",
        occurred_at=date(2025, 1, 10),
        equipment_name="温度センサーA",
        symptom="過熱により停止",
        cause="センサー劣化",
        action_taken="センサー交換",
        cost=50000, downtime_hours=2.0, failure_mode_id=mode1.id,
    )
    r2 = repo.create(
        original_text="コンプレッサー異音",
        occurred_at=date(2025, 2, 20),
        equipment_name="コンプレッサーB",
        symptom="異音が発生",
        cause="ベアリング摩耗",
        action_taken="ベアリング交換",
        cost=120000, downtime_hours=4.0, failure_mode_id=mode2.id,
    )
    r3 = repo.create(
        original_text="ポンプ漏れ",
        occurred_at=date(2025, 3, 5),
        equipment_name="ポンプC",
        symptom="オイル漏れ発生",
        cause="Oリング破損",
        action_taken="Oリング交換",
        cost=30000, downtime_hours=1.5, failure_mode_id=mode1.id,
    )
    return r1, r2, r3, mode1, mode2


class TestSearchListAPI:
    def test_search_requires_auth(self, api_client):
        assert api_client.get("/api/reports").status_code == 401

    def test_search_returns_200_with_no_filters(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        res = api_client.get("/api/reports", headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["success"] is True

    def test_search_response_has_required_fields(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = api_client.get("/api/reports", headers=admin_headers).json()["data"]
        for field in ["reports", "total", "page", "per_page"]:
            assert field in data

    def test_search_returns_all_reports_when_no_keyword(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = api_client.get("/api/reports", headers=admin_headers).json()["data"]
        assert data["total"] == 3

    def test_search_by_keyword_uses_faiss_ids(self, api_client, admin_headers, db_session):
        """FAISSが返したIDのみがDBから取得される"""
        r1, r2, r3, *_ = _seed_reports(db_session)
        with patch("app.api.reports.vector_store.search", return_value=[r1.id]):
            data = api_client.get("/api/reports?keyword=温度センサー", headers=admin_headers).json()["data"]
        assert data["total"] == 1
        assert data["reports"][0]["equipment_name"] == "温度センサーA"

    def test_search_by_keyword_faiss_empty_returns_empty(self, api_client, admin_headers, db_session):
        """FAISSが空リストを返した場合は0件"""
        _seed_reports(db_session)
        with patch("app.api.reports.vector_store.search", return_value=[]):
            data = api_client.get("/api/reports?keyword=存在しないキーワード", headers=admin_headers).json()["data"]
        assert data["total"] == 0
        assert data["reports"] == []

    def test_search_with_from_date_filter(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = api_client.get("/api/reports?from=2025-02-01", headers=admin_headers).json()["data"]
        assert data["total"] == 2

    def test_search_with_to_date_filter(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = api_client.get("/api/reports?to=2025-01-31", headers=admin_headers).json()["data"]
        assert data["total"] == 1

    def test_search_with_failure_mode_id_filter(self, api_client, admin_headers, db_session):
        r1, r2, r3, mode1, mode2 = _seed_reports(db_session)
        data = api_client.get(f"/api/reports?failure_mode_id={mode1.id}", headers=admin_headers).json()["data"]
        assert data["total"] == 2

    def test_search_sort_by_cost_desc(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        reports = api_client.get("/api/reports?sort=cost&order=desc", headers=admin_headers).json()["data"]["reports"]
        costs = [r["cost"] for r in reports if r["cost"] is not None]
        assert costs == sorted(costs, reverse=True)

    def test_search_sort_by_occurred_at_asc(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        reports = api_client.get("/api/reports?sort=occurred_at&order=asc", headers=admin_headers).json()["data"]["reports"]
        dates = [r["occurred_at"] for r in reports]
        assert dates == sorted(dates)

    def test_search_pagination(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = api_client.get("/api/reports?per_page=2&page=1", headers=admin_headers).json()["data"]
        assert len(data["reports"]) == 2
        assert data["total"] == 3

    def test_search_pagination_page2(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        data = api_client.get("/api/reports?per_page=2&page=2", headers=admin_headers).json()["data"]
        assert len(data["reports"]) == 1

    def test_search_reports_include_failure_mode_name(self, api_client, admin_headers, db_session):
        _seed_reports(db_session)
        reports = api_client.get("/api/reports", headers=admin_headers).json()["data"]["reports"]
        assert all("failure_mode" in r for r in reports)


class TestSearchDetailAPI:
    def test_get_by_id_returns_200(self, api_client, admin_headers, db_session):
        r1, *_ = _seed_reports(db_session)
        res = api_client.get(f"/api/reports/{r1.id}", headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["success"] is True

    def test_get_by_id_returns_all_fields(self, api_client, admin_headers, db_session):
        r1, *_ = _seed_reports(db_session)
        data = api_client.get(f"/api/reports/{r1.id}", headers=admin_headers).json()["data"]
        for field in ["id", "original_text", "occurred_at", "equipment_name",
                      "symptom", "cause", "action_taken", "cost", "downtime_hours",
                      "failure_mode", "source", "created_at"]:
            assert field in data

    def test_get_by_id_returns_correct_values(self, api_client, admin_headers, db_session):
        r1, *_ = _seed_reports(db_session)
        data = api_client.get(f"/api/reports/{r1.id}", headers=admin_headers).json()["data"]
        assert data["equipment_name"] == "温度センサーA"
        assert data["cost"] == 50000
        assert data["failure_mode"] == "電気系故障"

    def test_get_by_id_not_found_returns_404(self, api_client, admin_headers):
        res = api_client.get("/api/reports/99999", headers=admin_headers)
        assert res.status_code == 404
        assert res.json()["detail"]["code"] == "NOT_FOUND"

    def test_get_by_id_requires_auth(self, api_client):
        assert api_client.get("/api/reports/1").status_code == 401

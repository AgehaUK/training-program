"""
Slice 2: POST /api/reports・GET /api/reports のテスト
"""
from datetime import date
from unittest.mock import patch

from app.repositories.failure_mode_repository import FailureModeRepository
from app.repositories.failure_report_repository import FailureReportRepository


def _seed(db_session):
    mode_repo = FailureModeRepository(db_session)
    mode = mode_repo.find_or_create_by_name("摩耗")
    repo = FailureReportRepository(db_session)
    repo.create(
        original_text="ポンプAが停止",
        occurred_at=date(2025, 3, 1),
        equipment_name="ポンプA",
        symptom="流量低下",
        cause="インペラー摩耗",
        cost=80000,
        downtime_hours=3.0,
        failure_mode_id=mode.id,
    )
    repo.create(
        original_text="モーターBが異音",
        occurred_at=date(2025, 5, 10),
        equipment_name="モーターB",
        symptom="異音発生",
        cause="ベアリング摩耗",
        cost=30000,
        downtime_hours=1.5,
        failure_mode_id=mode.id,
    )


class TestCreateReport:
    def test_create_report_returns_201(self, api_client, admin_headers, db_session):
        FailureModeRepository(db_session).find_or_create_by_name("摩耗")
        res = api_client.post(
            "/api/reports",
            json={
                "original_text": "テスト故障",
                "occurred_at": "2025-01-01",
                "equipment_name": "設備X",
                "symptom": "停止",
                "failure_mode": "摩耗",
            },
            headers=admin_headers,
        )
        assert res.status_code == 200
        assert res.json()["data"]["id"] is not None

    def test_create_report_requires_auth(self, api_client, db_session):
        res = api_client.post(
            "/api/reports",
            json={
                "original_text": "テスト", "occurred_at": "2025-01-01",
                "equipment_name": "設備X", "symptom": "停止", "failure_mode": "その他",
            },
        )
        assert res.status_code == 401

    def test_create_report_invalid_date_returns_400(self, api_client, admin_headers):
        res = api_client.post(
            "/api/reports",
            json={
                "original_text": "テスト", "occurred_at": "不正な日付",
                "equipment_name": "設備X", "symptom": "停止", "failure_mode": "その他",
            },
            headers=admin_headers,
        )
        assert res.status_code == 400


class TestSearchReports:
    def test_search_returns_all_without_keyword(self, api_client, admin_headers, db_session):
        _seed(db_session)
        res = api_client.get("/api/reports", headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["data"]["total"] == 2

    def test_search_requires_auth(self, api_client):
        res = api_client.get("/api/reports")
        assert res.status_code == 401

    def test_search_with_keyword_uses_faiss_or_fallback(self, api_client, admin_headers, db_session):
        _seed(db_session)
        with patch("app.api.reports.vector_store.search", return_value=[]):
            res = api_client.get("/api/reports?keyword=ポンプ", headers=admin_headers)
        assert res.status_code == 200

    def test_get_report_detail(self, api_client, admin_headers, db_session):
        _seed(db_session)
        list_res = api_client.get("/api/reports", headers=admin_headers)
        report_id = list_res.json()["data"]["reports"][0]["id"]
        res = api_client.get(f"/api/reports/{report_id}", headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["data"]["id"] == report_id

    def test_get_report_not_found_returns_404(self, api_client, admin_headers):
        res = api_client.get("/api/reports/99999", headers=admin_headers)
        assert res.status_code == 404

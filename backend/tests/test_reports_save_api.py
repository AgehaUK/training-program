"""
Slice 2: POST /api/reports, GET /api/failure-modes, POST /api/reports/sample のテスト
"""
from unittest.mock import patch


class TestReportSaveAPI:
    def test_post_reports_success_returns_200(self, api_client, admin_headers):
        res = api_client.post(
            "/api/reports",
            json={
                "original_text": "2025年3月15日、射出成形機A号機にて異音が発生し停止。",
                "occurred_at": "2025-03-15",
                "equipment_name": "射出成形機A号機",
                "symptom": "異音が発生し停止",
                "cause": "インバーター劣化",
                "action_taken": "インバーター交換",
                "cost": 80000,
                "downtime_hours": 4.0,
                "failure_mode": "電気系故障",
            },
            headers=admin_headers,
        )
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert "id" in res.json()["data"]

    def test_post_reports_creates_new_failure_mode_if_not_exists(self, api_client, admin_headers):
        res = api_client.post(
            "/api/reports",
            json={
                "original_text": "新しい故障モードのテスト",
                "occurred_at": "2025-06-01",
                "equipment_name": "設備X",
                "symptom": "異常停止",
                "failure_mode": "新規故障モード",
            },
            headers=admin_headers,
        )
        assert res.status_code == 200
        assert res.json()["success"] is True

    def test_post_reports_missing_required_fields_returns_422(self, api_client, admin_headers):
        res = api_client.post(
            "/api/reports",
            json={"original_text": "テスト"},
            headers=admin_headers,
        )
        assert res.status_code == 422

    def test_post_reports_invalid_date_returns_400(self, api_client, admin_headers):
        res = api_client.post(
            "/api/reports",
            json={
                "original_text": "テスト", "occurred_at": "not-a-date",
                "equipment_name": "設備A", "symptom": "停止", "failure_mode": "電気系故障",
            },
            headers=admin_headers,
        )
        assert res.status_code == 400

    def test_post_reports_requires_auth(self, api_client):
        res = api_client.post(
            "/api/reports",
            json={"original_text": "テスト", "occurred_at": "2025-01-01",
                  "equipment_name": "設備A", "symptom": "停止", "failure_mode": "その他"},
        )
        assert res.status_code == 401


class TestFailureModesAPI:
    def test_get_failure_modes_returns_list(self, api_client, admin_headers):
        res = api_client.get("/api/failure-modes", headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert isinstance(res.json()["data"], list)

    def test_get_failure_modes_requires_auth(self, api_client):
        assert api_client.get("/api/failure-modes").status_code == 401

    def test_get_failure_modes_returns_correct_structure(self, api_client, admin_headers):
        api_client.post(
            "/api/reports",
            json={"original_text": "テスト", "occurred_at": "2025-01-01",
                  "equipment_name": "設備A", "symptom": "停止", "failure_mode": "電気系故障"},
            headers=admin_headers,
        )
        data = api_client.get("/api/failure-modes", headers=admin_headers).json()["data"]
        if data:
            assert "id" in data[0]
            assert "name" in data[0]


class TestSampleInsertAPI:
    def test_post_sample_returns_200(self, api_client, admin_headers):
        from app.services.llm_service import StructurizedData
        mock_result = StructurizedData({
            "occurred_at": "2025-01-10", "equipment_name": "設備A", "symptom": "停止",
            "cause": "劣化", "action_taken": "交換", "cost": 50000,
            "downtime_hours": 2.0, "failure_mode": "その他",
        })
        with patch("app.api.reports.llm_service.structurize", return_value=mock_result), \
             patch("app.api.reports.vector_store.add"):
            res = api_client.post("/api/reports/sample", headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert res.json()["data"]["inserted_count"] > 0

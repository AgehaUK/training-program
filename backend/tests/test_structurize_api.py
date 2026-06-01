"""
Slice 1: POST /api/reports/structurize のテスト
"""
from unittest.mock import MagicMock, patch


MOCK_STRUCTURIZED = {
    "occurred_at": "2023-12-05",
    "equipment_name": "温度センサー",
    "symptom": "温度センサー故障",
    "cause": None,
    "action_taken": None,
    "cost": 50000,
    "downtime_hours": 3.0,
    "failure_mode": "電気系故障",
}


class TestStructurizeAPI:
    def test_structurize_success_returns_200(self, api_client, admin_headers):
        mock_result = MagicMock()
        mock_result.model_dump.return_value = MOCK_STRUCTURIZED

        with patch("app.api.reports.llm_service.structurize", return_value=mock_result):
            res = api_client.post(
                "/api/reports/structurize",
                json={"text": "2023年12月5日、温度センサー故障。停止3時間、部品代5万円"},
                headers=admin_headers,
            )

        assert res.status_code == 200
        data = res.json()["data"]
        assert data["equipment_name"] == "温度センサー"
        assert data["cost"] == 50000
        assert data["downtime_hours"] == 3.0

    def test_structurize_returns_all_8_fields(self, api_client, admin_headers):
        mock_result = MagicMock()
        mock_result.model_dump.return_value = MOCK_STRUCTURIZED

        with patch("app.api.reports.llm_service.structurize", return_value=mock_result):
            res = api_client.post(
                "/api/reports/structurize",
                json={"text": "テスト故障報告"},
                headers=admin_headers,
            )

        data = res.json()["data"]
        for field in ["occurred_at", "equipment_name", "symptom", "cause",
                      "action_taken", "cost", "downtime_hours", "failure_mode"]:
            assert field in data

    def test_structurize_requires_auth(self, api_client):
        """認証なしは 401"""
        res = api_client.post("/api/reports/structurize", json={"text": "テスト"})
        assert res.status_code == 401

    def test_structurize_llm_error_returns_500(self, api_client, admin_headers):
        with patch("app.api.reports.llm_service.structurize", side_effect=Exception("API Error")):
            res = api_client.post(
                "/api/reports/structurize",
                json={"text": "テスト故障報告"},
                headers=admin_headers,
            )
        assert res.status_code == 500
        assert res.json()["detail"]["code"] == "LLM_API_ERROR"

    def test_structurize_nullable_fields_can_be_none(self, api_client, admin_headers):
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {
            "occurred_at": None, "equipment_name": "設備A", "symptom": "動作停止",
            "cause": None, "action_taken": None, "cost": None,
            "downtime_hours": None, "failure_mode": None,
        }
        with patch("app.api.reports.llm_service.structurize", return_value=mock_result):
            res = api_client.post(
                "/api/reports/structurize",
                json={"text": "設備Aが停止"},
                headers=admin_headers,
            )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["cause"] is None
        assert data["cost"] is None

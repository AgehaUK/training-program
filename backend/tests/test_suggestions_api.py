"""
Slice 4: POST /api/dashboard/suggestions のテスト
"""
from unittest.mock import patch


class TestSuggestionsAPI:
    def test_suggestions_requires_auth(self, api_client):
        res = api_client.post("/api/dashboard/suggestions", json={})
        assert res.status_code == 401

    def test_suggestions_returns_text(self, api_client, admin_headers):
        mock_text = "• 定期点検を強化してください\n• コスト削減のため予防保全を推進してください"
        with patch("app.api.dashboard.llm_service.generate_suggestions", return_value=mock_text):
            res = api_client.post("/api/dashboard/suggestions", json={}, headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert res.json()["data"] == mock_text

    def test_suggestions_accepts_filters(self, api_client, admin_headers):
        with patch("app.api.dashboard.llm_service.generate_suggestions", return_value="示唆テキスト"):
            res = api_client.post(
                "/api/dashboard/suggestions",
                json={"from_date": "2025-01-01", "to_date": "2025-12-31"},
                headers=admin_headers,
            )
        assert res.status_code == 200

    def test_suggestions_llm_error_returns_500(self, api_client, admin_headers):
        with patch("app.api.dashboard.llm_service.generate_suggestions",
                   side_effect=Exception("API Error")):
            res = api_client.post("/api/dashboard/suggestions", json={}, headers=admin_headers)
        assert res.status_code == 500
        assert res.json()["detail"]["code"] == "LLM_ERROR"

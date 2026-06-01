"""
認証・ユーザー管理 API のテスト
"""


class TestLogin:
    def test_login_success_returns_token(self, api_client):
        res = api_client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "admin1234"},
        )
        assert res.status_code == 200
        assert "access_token" in res.json()
        assert res.json()["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, api_client):
        res = api_client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "wrongpass"},
        )
        assert res.status_code == 401

    def test_login_unknown_user_returns_401(self, api_client):
        res = api_client.post(
            "/api/auth/login",
            data={"username": "nobody", "password": "pass"},
        )
        assert res.status_code == 401


class TestGetMe:
    def test_get_me_returns_current_user(self, api_client, admin_headers):
        res = api_client.get("/api/auth/me", headers=admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    def test_get_me_without_token_returns_401(self, api_client):
        assert api_client.get("/api/auth/me").status_code == 401

    def test_get_me_with_invalid_token_returns_401(self, api_client):
        res = api_client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert res.status_code == 401


class TestUserManagement:
    def test_list_users_admin_only(self, api_client, admin_headers):
        res = api_client.get("/api/users", headers=admin_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_list_users_user_forbidden(self, api_client, user_headers):
        assert api_client.get("/api/users", headers=user_headers).status_code == 403

    def test_create_user_by_admin(self, api_client, admin_headers):
        res = api_client.post(
            "/api/users",
            json={"username": "newuser", "password": "pass1234", "role": "user"},
            headers=admin_headers,
        )
        assert res.status_code == 201
        assert res.json()["username"] == "newuser"

    def test_create_duplicate_user_returns_400(self, api_client, admin_headers):
        api_client.post("/api/users",
                        json={"username": "dup", "password": "p", "role": "user"},
                        headers=admin_headers)
        res = api_client.post("/api/users",
                              json={"username": "dup", "password": "p", "role": "user"},
                              headers=admin_headers)
        assert res.status_code == 400

    def test_delete_user_by_admin(self, api_client, admin_headers):
        create_res = api_client.post(
            "/api/users",
            json={"username": "todelete", "password": "pass", "role": "user"},
            headers=admin_headers,
        )
        user_id = create_res.json()["id"]
        res = api_client.delete(f"/api/users/{user_id}", headers=admin_headers)
        assert res.status_code == 204

    def test_delete_self_returns_400(self, api_client, admin_headers, db_session):
        from app.models.user import User
        admin = db_session.query(User).filter(User.username == "admin").first()
        res = api_client.delete(f"/api/users/{admin.id}", headers=admin_headers)
        assert res.status_code == 400

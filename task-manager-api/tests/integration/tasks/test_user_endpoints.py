from __future__ import annotations


def _register_login(client, email: str = "u@example.com", password: str = "Password1") -> str:
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": "User"},
    )
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestAuthEnforcement:
    def test_list_users_requires_auth(self, client):
        assert client.get("/users/").status_code == 401

    def test_get_user_requires_auth(self, client):
        assert client.get("/users/some-id").status_code == 401


class TestListUsers:
    def test_returns_registered_users(self, client):
        token = _register_login(client, "a@example.com")
        _register_login(client, "b@example.com")
        resp = client.get("/users/", headers=_auth(token))
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_response_contains_expected_fields(self, client):
        token = _register_login(client, "c@example.com")
        resp = client.get("/users/", headers=_auth(token))
        assert resp.status_code == 200
        for user in resp.json():
            assert "id" in user
            assert "email" in user
            assert "password_hash" not in user
            assert "failed_login_attempts" not in user
            assert "lockout_until" not in user


class TestGetUser:
    def test_get_user_by_id(self, client):
        token = _register_login(client, "d@example.com")
        me = client.get("/auth/me", headers=_auth(token)).json()
        resp = client.get(f"/users/{me['id']}", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["id"] == me["id"]

    def test_get_nonexistent_user_returns_404(self, client):
        token = _register_login(client, "e@example.com")
        assert client.get("/users/nonexistent-id", headers=_auth(token)).status_code == 404

    def test_any_authenticated_user_can_get_any_user(self, client):
        token_a = _register_login(client, "f@example.com")
        token_b = _register_login(client, "g@example.com")
        me_a = client.get("/auth/me", headers=_auth(token_a)).json()
        resp = client.get(f"/users/{me_a['id']}", headers=_auth(token_b))
        assert resp.status_code == 200

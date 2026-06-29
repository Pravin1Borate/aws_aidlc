import pytest
from fastapi.testclient import TestClient


def register(client: TestClient, email: str = "user@example.com", password: str = "password123"):
    return client.post("/auth/register", json={"email": email, "password": password})


def login(client: TestClient, email: str = "user@example.com", password: str = "password123"):
    return client.post("/auth/login", json={"email": email, "password": password})


@pytest.mark.integration
class TestRegisterEndpoint:
    def test_register_success_returns_201(self, client: TestClient):  # US-01
        response = register(client)
        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "user@example.com"
        assert "id" in body
        assert "password_hash" not in body

    def test_register_duplicate_returns_409(self, client: TestClient):  # US-01
        register(client)
        response = register(client)
        assert response.status_code == 409

    def test_register_invalid_email_returns_422(self, client: TestClient):
        response = client.post("/auth/register", json={"email": "notanemail", "password": "password123"})
        assert response.status_code == 422

    def test_register_short_password_returns_422(self, client: TestClient):
        response = client.post("/auth/register", json={"email": "a@b.com", "password": "short"})
        assert response.status_code == 422


@pytest.mark.integration
class TestLoginEndpoint:
    def test_login_success_returns_token(self, client: TestClient):  # US-02
        register(client)
        response = login(client)
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0

    def test_login_wrong_password_returns_401(self, client: TestClient):  # US-02
        register(client)
        response = client.post("/auth/login", json={"email": "user@example.com", "password": "wrongpassword"})
        assert response.status_code == 401

    def test_login_unknown_email_returns_401(self, client: TestClient):
        response = login(client, email="ghost@example.com")
        assert response.status_code == 401

    def test_login_returns_no_password_in_response(self, client: TestClient):
        register(client)
        body = login(client).json()
        assert "password" not in body
        assert "password_hash" not in body


@pytest.mark.integration
class TestMeEndpoint:
    def test_me_with_valid_token(self, client: TestClient):  # US-03
        register(client)
        token = login(client).json()["access_token"]
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["email"] == "user@example.com"

    def test_me_without_token_returns_401(self, client: TestClient):  # US-03
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client: TestClient):
        response = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert response.status_code == 401


@pytest.mark.integration
class TestLogoutEndpoint:
    def test_logout_success(self, client: TestClient):  # US-04
        register(client)
        token = login(client).json()["access_token"]
        response = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

    def test_me_after_logout_returns_401(self, client: TestClient):  # US-04
        register(client)
        token = login(client).json()["access_token"]
        client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


@pytest.mark.integration
class TestHealthEndpoints:
    def test_health_live(self, client: TestClient):
        assert client.get("/health/live").status_code == 200

    def test_health_ready(self, client: TestClient):
        assert client.get("/health/ready").status_code == 200

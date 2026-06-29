import pytest
from fastapi.testclient import TestClient
from pathlib import Path


@pytest.mark.unit
class TestHealthEndpoints:
    def test_liveness_returns_ok(self, client: TestClient):
        response = client.get("/health/live")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["service"] == "task-manager-api"

    def test_readiness_returns_ready_when_configured(self, client: TestClient, patch_settings):
        response = client.get("/health/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["checks"]["jwt_config"] is True
        assert body["checks"]["data_dir"] is True

    def test_readiness_returns_degraded_when_data_dir_missing(
        self, client: TestClient, patch_settings, tmp_path: Path, monkeypatch
    ):
        import src.config as cfg
        monkeypatch.setattr(cfg.settings, "DATA_DIR", str(tmp_path / "nonexistent"))
        response = client.get("/health/ready")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "degraded"
        assert body["checks"]["data_dir"] is False

    def test_liveness_no_auth_required(self, client: TestClient):
        response = client.get("/health/live")
        assert response.status_code == 200

    def test_readiness_no_auth_required(self, client: TestClient):
        response = client.get("/health/ready")
        assert response.status_code in (200, 503)

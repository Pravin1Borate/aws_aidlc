import pytest
from pathlib import Path
from fastapi.testclient import TestClient

TEST_JWT_SECRET = "test-secret-key-for-testing-only-32chars"


@pytest.fixture(autouse=True)
def clear_token_blacklist():
    import src.core.security as security_module
    security_module._blacklist.clear()
    yield
    security_module._blacklist.clear()


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def patch_settings(tmp_data_dir: Path, monkeypatch):
    import src.config as config_module
    monkeypatch.setattr(config_module.settings, "JWT_SECRET_KEY", TEST_JWT_SECRET)
    monkeypatch.setattr(config_module.settings, "DATA_DIR", str(tmp_data_dir))
    monkeypatch.setattr(config_module.settings, "JWT_EXPIRY_MINUTES", 60)
    return config_module.settings


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from src.core.rate_limiter import limiter
    limiter._storage.reset()
    yield


@pytest.fixture
def client(patch_settings, tmp_data_dir: Path):
    from src.main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

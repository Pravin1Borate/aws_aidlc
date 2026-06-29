import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

from src.auth.repository import UserRepository
from src.auth.schemas import LoginRequest, User, UserCreate
from src.auth.service import AuthService, _LOCKOUT_THRESHOLD
from src.core.errors import ConflictError, UnauthorizedError
from src.core.security import hash_password
from src.core.storage import JsonFileStorage


def make_repo(tmp_data_dir: Path) -> UserRepository:
    storage = JsonFileStorage(str(tmp_data_dir / "users.json"))
    return UserRepository(storage)


def make_service(tmp_data_dir: Path) -> AuthService:
    return AuthService(make_repo(tmp_data_dir))


@pytest.mark.unit
class TestRegister:
    def test_register_success(self, patch_settings, tmp_data_dir):  # US-01
        svc = make_service(tmp_data_dir)
        result = svc.register(UserCreate(email="new@example.com", password="password123"))
        assert result.email == "new@example.com"
        assert str(result.id) != ""

    def test_register_duplicate_email_raises_conflict(self, patch_settings, tmp_data_dir):  # US-01
        svc = make_service(tmp_data_dir)
        svc.register(UserCreate(email="dup@example.com", password="password123"))
        with pytest.raises(ConflictError):
            svc.register(UserCreate(email="dup@example.com", password="other1234"))

    def test_register_email_stored_lowercase(self, patch_settings, tmp_data_dir):
        svc = make_service(tmp_data_dir)
        result = svc.register(UserCreate(email="Upper@Example.COM", password="password123"))
        assert result.email == "upper@example.com"

    def test_register_password_not_in_response(self, patch_settings, tmp_data_dir):
        svc = make_service(tmp_data_dir)
        result = svc.register(UserCreate(email="safe@example.com", password="password123"))
        assert not hasattr(result, "password_hash")


@pytest.mark.unit
class TestLogin:
    def test_login_success_returns_token(self, patch_settings, tmp_data_dir):  # US-02
        svc = make_service(tmp_data_dir)
        svc.register(UserCreate(email="login@example.com", password="password123"))
        result = svc.login(LoginRequest(email="login@example.com", password="password123"))
        assert result.access_token != ""
        assert result.token_type == "bearer"

    def test_login_wrong_password_raises(self, patch_settings, tmp_data_dir):  # US-02
        svc = make_service(tmp_data_dir)
        svc.register(UserCreate(email="bad@example.com", password="password123"))
        with pytest.raises(UnauthorizedError):
            svc.login(LoginRequest(email="bad@example.com", password="wrongpassword"))

    def test_login_wrong_password_increments_counter(self, patch_settings, tmp_data_dir):  # US-02
        svc = make_service(tmp_data_dir)
        svc.register(UserCreate(email="counter@example.com", password="password123"))
        with pytest.raises(UnauthorizedError):
            svc.login(LoginRequest(email="counter@example.com", password="wrong"))
        user = make_repo(tmp_data_dir).find_by_email("counter@example.com")
        assert user.failed_login_attempts == 1

    def test_login_fifth_failure_locks_account(self, patch_settings, tmp_data_dir):  # US-02
        svc = make_service(tmp_data_dir)
        svc.register(UserCreate(email="lockme@example.com", password="password123"))
        for _ in range(_LOCKOUT_THRESHOLD):
            with pytest.raises(UnauthorizedError):
                svc.login(LoginRequest(email="lockme@example.com", password="wrong"))
        user = make_repo(tmp_data_dir).find_by_email("lockme@example.com")
        assert user.lockout_until is not None
        assert user.lockout_until > datetime.now(timezone.utc)

    def test_login_locked_account_raises(self, patch_settings, tmp_data_dir):  # US-02
        svc = make_service(tmp_data_dir)
        svc.register(UserCreate(email="locked@example.com", password="password123"))
        repo = make_repo(tmp_data_dir)
        user = repo.find_by_email("locked@example.com")
        user.lockout_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        repo.save(user)
        with pytest.raises(UnauthorizedError, match="temporarily locked"):
            svc.login(LoginRequest(email="locked@example.com", password="password123"))

    def test_login_success_resets_counter(self, patch_settings, tmp_data_dir):  # US-02
        svc = make_service(tmp_data_dir)
        svc.register(UserCreate(email="reset@example.com", password="password123"))
        with pytest.raises(UnauthorizedError):
            svc.login(LoginRequest(email="reset@example.com", password="wrong"))
        svc.login(LoginRequest(email="reset@example.com", password="password123"))
        user = make_repo(tmp_data_dir).find_by_email("reset@example.com")
        assert user.failed_login_attempts == 0
        assert user.lockout_until is None

    def test_login_unknown_email_raises_same_error(self, patch_settings, tmp_data_dir):
        svc = make_service(tmp_data_dir)
        with pytest.raises(UnauthorizedError, match="Invalid credentials"):
            svc.login(LoginRequest(email="nobody@example.com", password="password123"))


@pytest.mark.unit
class TestLogout:
    def test_logout_blacklists_token(self, patch_settings, tmp_data_dir):  # US-04
        svc = make_service(tmp_data_dir)
        svc.register(UserCreate(email="logout@example.com", password="password123"))
        token_resp = svc.login(LoginRequest(email="logout@example.com", password="password123"))
        svc.logout(token_resp.access_token)
        from src.core.security import is_blacklisted
        assert is_blacklisted(token_resp.access_token) is True

    def test_logout_invalid_token_raises(self, patch_settings, tmp_data_dir):  # US-04
        svc = make_service(tmp_data_dir)
        with pytest.raises(UnauthorizedError):
            svc.logout("not.a.valid.token")


@pytest.mark.unit
class TestGetCurrentUser:
    def test_get_current_user_valid_token(self, patch_settings, tmp_data_dir):  # US-03
        svc = make_service(tmp_data_dir)
        svc.register(UserCreate(email="me@example.com", password="password123"))
        token_resp = svc.login(LoginRequest(email="me@example.com", password="password123"))
        user = svc.get_current_user(token_resp.access_token)
        assert user.email == "me@example.com"

    def test_get_current_user_expired_token_raises(self, patch_settings, tmp_data_dir):  # US-03
        from src.core.security import create_access_token
        token = create_access_token({"sub": "uid"}, expires_delta=timedelta(seconds=-1))
        svc = make_service(tmp_data_dir)
        with pytest.raises(UnauthorizedError):
            svc.get_current_user(token)

    def test_get_current_user_blacklisted_token_raises(self, patch_settings, tmp_data_dir):  # US-03
        svc = make_service(tmp_data_dir)
        svc.register(UserCreate(email="blk@example.com", password="password123"))
        token_resp = svc.login(LoginRequest(email="blk@example.com", password="password123"))
        svc.logout(token_resp.access_token)
        with pytest.raises(UnauthorizedError):
            svc.get_current_user(token_resp.access_token)

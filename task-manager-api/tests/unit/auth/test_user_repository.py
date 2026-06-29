import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.auth.repository import UserRepository
from src.auth.schemas import User
from src.core.storage import JsonFileStorage


def make_user(email: str = "test@example.com", user_id: str = "user-001") -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=user_id,
        email=email,
        password_hash="$2b$12$fakehash",
        full_name="Test User",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def repo(tmp_data_dir: Path) -> UserRepository:
    storage = JsonFileStorage(str(tmp_data_dir / "users.json"))
    return UserRepository(storage)


@pytest.mark.unit
class TestUserRepository:
    def test_save_and_find_by_email(self, repo):
        user = make_user(email="alice@example.com")
        repo.save(user)
        found = repo.find_by_email("alice@example.com")
        assert found is not None
        assert found.email == "alice@example.com"

    def test_save_and_find_by_id(self, repo):
        user = make_user(user_id="uid-999")
        repo.save(user)
        found = repo.find_by_id("uid-999")
        assert found is not None
        assert found.id == "uid-999"

    def test_find_by_email_not_found_returns_none(self, repo):
        assert repo.find_by_email("nobody@example.com") is None

    def test_find_by_id_not_found_returns_none(self, repo):
        assert repo.find_by_id("nonexistent-id") is None

    def test_save_updates_existing_user(self, repo):
        user = make_user(email="bob@example.com", user_id="uid-bob")
        repo.save(user)
        user.full_name = "Updated Name"
        repo.save(user)
        found = repo.find_by_id("uid-bob")
        assert found is not None
        assert found.full_name == "Updated Name"

    def test_email_case_insensitive_lookup(self, repo):
        user = make_user(email="carol@example.com")
        repo.save(user)
        assert repo.find_by_email("CAROL@EXAMPLE.COM") is not None
        assert repo.find_by_email("Carol@Example.Com") is not None

    def test_save_multiple_users(self, repo):
        repo.save(make_user(email="u1@example.com", user_id="id-1"))
        repo.save(make_user(email="u2@example.com", user_id="id-2"))
        assert repo.find_by_email("u1@example.com") is not None
        assert repo.find_by_email("u2@example.com") is not None

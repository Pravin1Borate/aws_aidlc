from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.core.errors import NotFoundError
from src.users.schemas import UserSummary
from src.users.service import UserService


def _make_summary(user_id: str = "u1", email: str = "u@example.com") -> UserSummary:
    return UserSummary(id=user_id, email=email, full_name="Test User")


@pytest.fixture
def user_repo():
    return MagicMock()


@pytest.fixture
def svc(user_repo):
    return UserService(user_repo)


class TestListUsers:
    def test_returns_all_users(self, svc, user_repo):
        user_repo.find_all.return_value = [_make_summary("u1"), _make_summary("u2")]
        result = svc.list_users()
        assert len(result) == 2

    def test_returns_empty_list_when_no_users(self, svc, user_repo):
        user_repo.find_all.return_value = []
        assert svc.list_users() == []

    def test_delegates_to_repository(self, svc, user_repo):
        user_repo.find_all.return_value = []
        svc.list_users()
        user_repo.find_all.assert_called_once()


class TestGetById:
    def test_returns_user_when_found(self, svc, user_repo):
        user_repo.find_by_id.return_value = _make_summary("u1")
        result = svc.get_by_id("u1")
        assert result.id == "u1"

    def test_raises_404_when_not_found(self, svc, user_repo):
        user_repo.find_by_id.return_value = None
        with pytest.raises(NotFoundError):
            svc.get_by_id("missing")

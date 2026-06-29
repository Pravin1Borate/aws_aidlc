from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.core.errors import ForbiddenError, NotFoundError
from src.tasks.schemas import (
    Task,
    TaskCreate,
    TaskFilter,
    TaskPatch,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)
from src.tasks.service import TaskService
from src.users.schemas import UserSummary

OWNER_ID = "owner-uuid"
ASSIGNEE_ID = "assignee-uuid"
OTHER_ID = "other-uuid"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_task(**overrides) -> Task:
    defaults = dict(
        id="task-1",
        title="Test",
        description=None,
        status=TaskStatus.todo,
        priority=TaskPriority.medium,
        due_date=None,
        category=None,
        tags=[],
        owner_id=OWNER_ID,
        assignee_id=None,
        deleted_at=None,
        created_at=_now(),
        updated_at=_now(),
    )
    defaults.update(overrides)
    return Task(**defaults)


def _make_user(user_id: str = ASSIGNEE_ID, email: str = "a@example.com") -> UserSummary:
    return UserSummary(id=user_id, email=email, full_name="A")


@pytest.fixture
def task_repo():
    return MagicMock()


@pytest.fixture
def user_repo():
    return MagicMock()


@pytest.fixture
def svc(task_repo, user_repo):
    return TaskService(task_repo, user_repo)


# ── create ────────────────────────────────────────────────────────────────


class TestCreate:
    def test_creates_task_with_defaults(self, svc, task_repo, user_repo):
        user_repo.find_by_id.return_value = None
        user_repo.find_by_email.return_value = None
        task_repo.save.side_effect = lambda t: t
        result = svc.create(TaskCreate(title="My Task"), caller_id=OWNER_ID)
        assert result.title == "My Task"
        assert result.owner_id == OWNER_ID
        assert result.status == TaskStatus.todo
        assert result.priority == TaskPriority.medium
        assert task_repo.save.called

    def test_resolves_assignee_by_id(self, svc, task_repo, user_repo):
        user_repo.find_by_id.return_value = _make_user()
        task_repo.save.side_effect = lambda t: t
        result = svc.create(TaskCreate(title="T", assignee_id=ASSIGNEE_ID), OWNER_ID)
        assert result.assignee_id == ASSIGNEE_ID

    def test_resolves_assignee_by_email(self, svc, task_repo, user_repo):
        user_repo.find_by_email.return_value = _make_user()
        task_repo.save.side_effect = lambda t: t
        result = svc.create(TaskCreate(title="T", assignee_email="a@example.com"), OWNER_ID)
        assert result.assignee_id == ASSIGNEE_ID

    def test_assignee_id_takes_precedence_over_email(self, svc, task_repo, user_repo):
        user_repo.find_by_id.return_value = _make_user(user_id="by-id-user")
        task_repo.save.side_effect = lambda t: t
        result = svc.create(
            TaskCreate(title="T", assignee_id="by-id-user", assignee_email="a@example.com"),
            OWNER_ID,
        )
        assert result.assignee_id == "by-id-user"
        user_repo.find_by_email.assert_not_called()

    def test_unknown_assignee_id_raises_404(self, svc, task_repo, user_repo):
        user_repo.find_by_id.return_value = None
        with pytest.raises(NotFoundError):
            svc.create(TaskCreate(title="T", assignee_id="unknown"), OWNER_ID)

    def test_unknown_assignee_email_raises_404(self, svc, task_repo, user_repo):
        user_repo.find_by_email.return_value = None
        with pytest.raises(NotFoundError):
            svc.create(TaskCreate(title="T", assignee_email="nope@x.com"), OWNER_ID)


# ── get_by_id ─────────────────────────────────────────────────────────────


class TestGetById:
    def test_returns_task_response(self, svc, task_repo):
        task_repo.find_by_id.return_value = _make_task()
        result = svc.get_by_id("task-1", OWNER_ID)
        assert isinstance(result, TaskResponse)
        assert result.id == "task-1"

    def test_raises_404_when_missing(self, svc, task_repo):
        task_repo.find_by_id.return_value = None
        with pytest.raises(NotFoundError):
            svc.get_by_id("missing", OWNER_ID)


# ── list_tasks ────────────────────────────────────────────────────────────


class TestListTasks:
    def test_returns_responses_and_total(self, svc, task_repo):
        tasks = [_make_task(id=f"t{i}") for i in range(3)]
        task_repo.find_filtered.return_value = (tasks, 3)
        items, total = svc.list_tasks(TaskFilter(), 10, 0)
        assert total == 3
        assert len(items) == 3

    def test_passes_filters_through(self, svc, task_repo):
        task_repo.find_filtered.return_value = ([], 0)
        svc.list_tasks(TaskFilter(status=TaskStatus.done), 5, 10)
        call_kwargs = task_repo.find_filtered.call_args.kwargs
        assert call_kwargs["status"] == TaskStatus.done
        assert call_kwargs["limit"] == 5
        assert call_kwargs["offset"] == 10


# ── full_update ───────────────────────────────────────────────────────────


class TestFullUpdate:
    def test_owner_can_update_title(self, svc, task_repo, user_repo):
        task_repo.find_by_id.return_value = _make_task()
        task_repo.save.side_effect = lambda t: t
        user_repo.find_by_id.return_value = None
        user_repo.find_by_email.return_value = None
        result = svc.full_update("task-1", TaskUpdate(title="New"), OWNER_ID)
        assert result.title == "New"

    def test_assignee_can_update_non_assignee_fields(self, svc, task_repo, user_repo):
        task_repo.find_by_id.return_value = _make_task(assignee_id=ASSIGNEE_ID)
        task_repo.save.side_effect = lambda t: t
        user_repo.find_by_id.return_value = None
        user_repo.find_by_email.return_value = None
        result = svc.full_update("task-1", TaskUpdate(title="By assignee"), ASSIGNEE_ID)
        assert result.title == "By assignee"

    def test_other_user_gets_403(self, svc, task_repo):
        task_repo.find_by_id.return_value = _make_task()
        with pytest.raises(ForbiddenError):
            svc.full_update("task-1", TaskUpdate(title="X"), OTHER_ID)

    def test_owner_id_immutable_after_update(self, svc, task_repo, user_repo):
        task_repo.find_by_id.return_value = _make_task()
        task_repo.save.side_effect = lambda t: t
        user_repo.find_by_id.return_value = None
        user_repo.find_by_email.return_value = None
        svc.full_update("task-1", TaskUpdate(title="X"), OWNER_ID)
        saved: Task = task_repo.save.call_args[0][0]
        assert saved.owner_id == OWNER_ID

    def test_assignee_cannot_change_assignee(self, svc, task_repo, user_repo):
        task_repo.find_by_id.return_value = _make_task(assignee_id=ASSIGNEE_ID)
        user_repo.find_by_id.return_value = _make_user(user_id="new-user")
        with pytest.raises(ForbiddenError):
            svc.full_update("task-1", TaskUpdate(title="X", assignee_id="new-user"), ASSIGNEE_ID)

    def test_not_found_raises_404(self, svc, task_repo):
        task_repo.find_by_id.return_value = None
        with pytest.raises(NotFoundError):
            svc.full_update("missing", TaskUpdate(title="X"), OWNER_ID)


# ── partial_update ────────────────────────────────────────────────────────


class TestPartialUpdate:
    def test_only_updates_provided_fields(self, svc, task_repo):
        task_repo.find_by_id.return_value = _make_task(
            status=TaskStatus.todo, priority=TaskPriority.low
        )
        task_repo.save.side_effect = lambda t: t
        result = svc.partial_update("task-1", TaskPatch(status=TaskStatus.done), OWNER_ID)
        assert result.status == TaskStatus.done
        assert result.priority == TaskPriority.low

    def test_tag_merge_remove_then_add(self, svc, task_repo):
        task_repo.find_by_id.return_value = _make_task(tags=["a", "b", "c"])
        task_repo.save.side_effect = lambda t: t
        result = svc.partial_update(
            "task-1", TaskPatch(tags=["d"], tags_remove=["b"]), OWNER_ID
        )
        assert set(result.tags) == {"a", "c", "d"}
        assert "b" not in result.tags

    def test_tag_remove_only(self, svc, task_repo):
        task_repo.find_by_id.return_value = _make_task(tags=["x", "y"])
        task_repo.save.side_effect = lambda t: t
        result = svc.partial_update("task-1", TaskPatch(tags_remove=["x"]), OWNER_ID)
        assert result.tags == ["y"]

    def test_assignee_cannot_change_assignee_in_patch(self, svc, task_repo, user_repo):
        task_repo.find_by_id.return_value = _make_task(assignee_id=ASSIGNEE_ID)
        user_repo.find_by_id.return_value = _make_user(user_id="new-user")
        with pytest.raises(ForbiddenError):
            svc.partial_update("task-1", TaskPatch(assignee_id="new-user"), ASSIGNEE_ID)

    def test_other_user_gets_403(self, svc, task_repo):
        task_repo.find_by_id.return_value = _make_task()
        with pytest.raises(ForbiddenError):
            svc.partial_update("task-1", TaskPatch(title="X"), OTHER_ID)


# ── delete ────────────────────────────────────────────────────────────────


class TestDelete:
    def test_owner_soft_deletes_task(self, svc, task_repo):
        task_repo.find_by_id.return_value = _make_task()
        task_repo.save.side_effect = lambda t: t
        svc.delete("task-1", OWNER_ID)
        saved: Task = task_repo.save.call_args[0][0]
        assert saved.deleted_at is not None

    def test_assignee_cannot_delete(self, svc, task_repo):
        task_repo.find_by_id.return_value = _make_task(assignee_id=ASSIGNEE_ID)
        with pytest.raises(ForbiddenError):
            svc.delete("task-1", ASSIGNEE_ID)

    def test_other_user_cannot_delete(self, svc, task_repo):
        task_repo.find_by_id.return_value = _make_task()
        with pytest.raises(ForbiddenError):
            svc.delete("task-1", OTHER_ID)

    def test_not_found_raises_404(self, svc, task_repo):
        task_repo.find_by_id.return_value = None
        with pytest.raises(NotFoundError):
            svc.delete("missing", OWNER_ID)

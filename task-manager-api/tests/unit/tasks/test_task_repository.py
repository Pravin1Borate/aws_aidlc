from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from src.core.storage import JsonFileStorage
from src.tasks.repository import TaskRepository
from src.tasks.schemas import Task, TaskPriority, TaskStatus


def _make_task(**overrides) -> Task:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id="task-1",
        title="Test Task",
        description=None,
        status=TaskStatus.todo,
        priority=TaskPriority.medium,
        due_date=None,
        category=None,
        tags=[],
        owner_id="user-1",
        assignee_id=None,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return Task(**defaults)


@pytest.fixture
def repo(patch_settings, tmp_data_dir):
    storage = JsonFileStorage(f"{tmp_data_dir}/tasks.json")
    return TaskRepository(storage)


class TestFindById:
    def test_returns_task_when_found(self, repo):
        repo.save(_make_task())
        found = repo.find_by_id("task-1")
        assert found is not None
        assert found.id == "task-1"

    def test_returns_none_when_not_found(self, repo):
        assert repo.find_by_id("nonexistent") is None

    def test_returns_none_for_soft_deleted(self, repo):
        repo.save(_make_task(deleted_at=datetime.now(timezone.utc)))
        assert repo.find_by_id("task-1") is None


class TestFindFiltered:
    def test_returns_only_active_tasks(self, repo):
        repo.save(_make_task(id="t1"))
        repo.save(_make_task(id="t2", deleted_at=datetime.now(timezone.utc)))
        tasks, total = repo.find_filtered(None, None, None, 100, 0)
        assert total == 1
        assert tasks[0].id == "t1"

    def test_filter_by_status(self, repo):
        repo.save(_make_task(id="t1", status=TaskStatus.todo))
        repo.save(_make_task(id="t2", status=TaskStatus.done))
        tasks, total = repo.find_filtered(TaskStatus.todo, None, None, 100, 0)
        assert total == 1
        assert tasks[0].status == TaskStatus.todo

    def test_filter_by_priority(self, repo):
        repo.save(_make_task(id="t1", priority=TaskPriority.high))
        repo.save(_make_task(id="t2", priority=TaskPriority.low))
        tasks, total = repo.find_filtered(None, TaskPriority.high, None, 100, 0)
        assert total == 1
        assert tasks[0].priority == TaskPriority.high

    def test_filter_by_due_date_returns_on_or_before(self, repo):
        repo.save(_make_task(id="t1", due_date=date(2024, 1, 1)))
        repo.save(_make_task(id="t2", due_date=date(2024, 6, 1)))
        tasks, total = repo.find_filtered(None, None, date(2024, 3, 1), 100, 0)
        assert total == 1
        assert tasks[0].id == "t1"

    def test_no_due_date_excluded_from_due_date_filter(self, repo):
        repo.save(_make_task(id="t1", due_date=None))
        tasks, total = repo.find_filtered(None, None, date(2024, 12, 31), 100, 0)
        assert total == 0

    def test_pagination_limit(self, repo):
        for i in range(5):
            repo.save(_make_task(id=f"t{i}"))
        tasks, total = repo.find_filtered(None, None, None, 2, 0)
        assert total == 5
        assert len(tasks) == 2

    def test_pagination_offset(self, repo):
        for i in range(5):
            repo.save(_make_task(id=f"t{i}"))
        tasks, total = repo.find_filtered(None, None, None, 2, 3)
        assert total == 5
        assert len(tasks) == 2

    def test_sort_due_date_asc_nulls_last(self, repo):
        repo.save(_make_task(id="t_june", due_date=date(2024, 6, 1)))
        repo.save(_make_task(id="t_none", due_date=None))
        repo.save(_make_task(id="t_jan", due_date=date(2024, 1, 1)))
        tasks, _ = repo.find_filtered(None, None, None, 100, 0)
        assert tasks[0].id == "t_jan"
        assert tasks[1].id == "t_june"
        assert tasks[2].id == "t_none"

    def test_multiple_filters_anded(self, repo):
        repo.save(_make_task(id="t1", status=TaskStatus.todo, priority=TaskPriority.high))
        repo.save(_make_task(id="t2", status=TaskStatus.done, priority=TaskPriority.high))
        repo.save(_make_task(id="t3", status=TaskStatus.todo, priority=TaskPriority.low))
        tasks, total = repo.find_filtered(TaskStatus.todo, TaskPriority.high, None, 100, 0)
        assert total == 1
        assert tasks[0].id == "t1"


class TestSave:
    def test_creates_new_task(self, repo):
        task = _make_task()
        saved = repo.save(task)
        assert saved.id == task.id

    def test_updates_existing_task(self, repo):
        task = _make_task()
        repo.save(task)
        task.title = "Updated Title"
        repo.save(task)
        found = repo.find_by_id(task.id)
        assert found is not None
        assert found.title == "Updated Title"

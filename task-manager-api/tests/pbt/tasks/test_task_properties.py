from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.tasks.schemas import Task, TaskPriority, TaskResponse, TaskStatus
from src.tasks.service import TaskService


# ─── helpers ─────────────────────────────────────────────────────────────


def _svc() -> TaskService:
    return TaskService(MagicMock(), MagicMock())


def _make_task(**kwargs) -> Task:
    now = datetime.now(timezone.utc)
    defaults: dict = dict(
        id="t1",
        title="Test",
        description=None,
        status=TaskStatus.todo,
        priority=TaskPriority.medium,
        due_date=None,
        category=None,
        tags=[],
        owner_id="owner-1",
        assignee_id=None,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(kwargs)
    return Task(**defaults)


tag_st = st.text(min_size=1, max_size=50).filter(str.strip)
tag_list_st = st.lists(tag_st, max_size=10)


# ─── tag merge properties ─────────────────────────────────────────────────


@given(existing=tag_list_st, to_add=tag_list_st, to_remove=tag_list_st)
def test_tag_merge_produces_no_duplicates(existing, to_add, to_remove):
    """Result contains no duplicate tags regardless of input."""
    result = _svc()._apply_tag_merge(existing, to_add, to_remove)
    assert len(result) == len(set(result))


@given(existing=tag_list_st, to_add=tag_list_st, to_remove=tag_list_st)
def test_tags_in_remove_absent_unless_re_added(existing, to_add, to_remove):
    """Tags listed in to_remove do not appear in result, unless also in to_add."""
    result = _svc()._apply_tag_merge(existing, to_add, to_remove)
    only_removed = set(to_remove) - set(to_add)
    for tag in only_removed:
        assert tag not in result


@given(existing=tag_list_st, to_add=tag_list_st)
def test_tag_merge_idempotent(existing, to_add):
    """Applying the same merge twice returns the same list."""
    svc = _svc()
    first = svc._apply_tag_merge(existing, to_add, [])
    second = svc._apply_tag_merge(first, to_add, [])
    assert first == second


@given(existing=tag_list_st, to_add=tag_list_st, to_remove=tag_list_st)
def test_tags_in_to_add_present_in_result(existing, to_add, to_remove):
    """Tags in to_add (not in to_remove) always appear in result."""
    result = _svc()._apply_tag_merge(existing, to_add, to_remove)
    for tag in to_add:
        if tag not in to_remove:
            assert tag in result


# ─── response invariants ──────────────────────────────────────────────────


@given(title=st.text(min_size=1, max_size=255))
def test_task_response_never_exposes_deleted_at(title):
    """TaskResponse must not include deleted_at field regardless of internal state."""
    task = _make_task(title=title, deleted_at=datetime.now(timezone.utc))
    response = _svc()._to_response(task)
    assert "deleted_at" not in response.model_dump()


@given(
    owner_id=st.text(min_size=1, max_size=36).filter(str.strip),
    title=st.text(min_size=1, max_size=255),
)
def test_owner_id_unchanged_in_response(owner_id, title):
    """owner_id in TaskResponse always equals the task's owner_id."""
    task = _make_task(owner_id=owner_id, title=title)
    response = _svc()._to_response(task)
    assert response.owner_id == owner_id


# ─── due_date filter invariant ────────────────────────────────────────────


@settings(max_examples=50)
@given(
    due_dates=st.lists(
        st.one_of(st.none(), st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))),
        min_size=1,
        max_size=20,
    ),
    filter_date=st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)),
)
def test_due_date_filter_never_returns_later_tasks(due_dates, filter_date):
    """After due_date filtering, no task in result has due_date > filter_date."""
    from src.core.storage import JsonFileStorage
    from src.tasks.repository import TaskRepository
    import tempfile, os

    now = datetime.now(timezone.utc)
    tasks = [
        _make_task(id=f"t{i}", due_date=d, created_at=now, updated_at=now)
        for i, d in enumerate(due_dates)
    ]
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        f.write("[]")
        tmp_path = f.name
    try:
        storage = JsonFileStorage(tmp_path)
        repo = TaskRepository(storage)
        for t in tasks:
            repo.save(t)
        result, _ = repo.find_filtered(None, None, filter_date, 1000, 0)
        for task in result:
            assert task.due_date is not None
            assert task.due_date <= filter_date
    finally:
        os.unlink(tmp_path)

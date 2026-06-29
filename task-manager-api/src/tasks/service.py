from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.core.errors import ForbiddenError, NotFoundError
from src.core.logging import get_logger
from src.tasks.repository import TaskRepository
from src.tasks.schemas import (
    Task,
    TaskCreate,
    TaskFilter,
    TaskPatch,
    TaskResponse,
    TaskUpdate,
)
from src.users.repository import UserReadRepository

logger = get_logger(__name__)


class TaskService:
    def __init__(
        self, task_repo: TaskRepository, user_read_repo: UserReadRepository
    ) -> None:
        self._task_repo = task_repo
        self._user_repo = user_read_repo

    # ── Public operations ─────────────────────────────────────────────────

    def create(self, data: TaskCreate, caller_id: str) -> TaskResponse:
        assignee_id = self._resolve_assignee(data.assignee_id, data.assignee_email)
        now = datetime.now(timezone.utc)
        task = Task(
            id=str(uuid.uuid4()),
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            due_date=data.due_date,
            category=data.category,
            tags=list(dict.fromkeys(data.tags)),
            owner_id=caller_id,
            assignee_id=assignee_id,
            deleted_at=None,
            created_at=now,
            updated_at=now,
        )
        self._task_repo.save(task)
        logger.info("task_created", extra={"task_id": task.id, "caller_id": caller_id})
        return self._to_response(task)

    def get_by_id(self, task_id: str, caller_id: str) -> TaskResponse:
        task = self._get_active_task(task_id)
        return self._to_response(task)

    def list_tasks(
        self, filters: TaskFilter, limit: int, offset: int
    ) -> tuple[list[TaskResponse], int]:
        tasks, total = self._task_repo.find_filtered(
            status=filters.status,
            priority=filters.priority,
            due_date_filter=filters.due_date,
            limit=limit,
            offset=offset,
        )
        return [self._to_response(t) for t in tasks], total

    def full_update(
        self, task_id: str, data: TaskUpdate, caller_id: str
    ) -> TaskResponse:
        task = self._get_active_task(task_id)
        self._check_access(task, caller_id)

        new_assignee_id = self._resolve_assignee(data.assignee_id, data.assignee_email)
        # BR-TASK-04.4: only owner may change assignee; preserve existing when not explicitly set
        if data.assignee_id is None and data.assignee_email is None:
            new_assignee_id = task.assignee_id
        elif new_assignee_id != task.assignee_id and caller_id != task.owner_id:
            raise ForbiddenError("Only the task owner can change the assignee")

        task.title = data.title
        task.description = data.description
        task.status = data.status
        task.priority = data.priority
        task.due_date = data.due_date
        task.category = data.category
        task.tags = list(dict.fromkeys(data.tags))
        task.assignee_id = new_assignee_id
        task.updated_at = datetime.now(timezone.utc)

        self._task_repo.save(task)
        logger.info("task_updated", extra={"task_id": task_id, "caller_id": caller_id})
        return self._to_response(task)

    def partial_update(
        self, task_id: str, data: TaskPatch, caller_id: str
    ) -> TaskResponse:
        task = self._get_active_task(task_id)
        self._check_access(task, caller_id)

        fields = data.model_fields_set
        assignee_changing = "assignee_id" in fields or "assignee_email" in fields
        # BR-TASK-05.5: only owner may change assignee
        if assignee_changing and caller_id != task.owner_id:
            raise ForbiddenError("Only the task owner can change the assignee")

        if "title" in fields:
            task.title = data.title  # type: ignore[assignment]
        if "description" in fields:
            task.description = data.description
        if "status" in fields:
            task.status = data.status  # type: ignore[assignment]
        if "priority" in fields:
            task.priority = data.priority  # type: ignore[assignment]
        if "due_date" in fields:
            task.due_date = data.due_date
        if "category" in fields:
            task.category = data.category
        if assignee_changing:
            task.assignee_id = self._resolve_assignee(data.assignee_id, data.assignee_email)

        # BR-TASK-05.6-7: remove first, then add (merge semantics)
        if "tags" in fields or "tags_remove" in fields:
            task.tags = self._apply_tag_merge(
                task.tags,
                data.tags or [],
                data.tags_remove or [],
            )

        task.updated_at = datetime.now(timezone.utc)
        self._task_repo.save(task)
        logger.info("task_patched", extra={"task_id": task_id, "caller_id": caller_id})
        return self._to_response(task)

    def delete(self, task_id: str, caller_id: str) -> None:
        task = self._get_active_task(task_id)
        self._check_access(task, caller_id, require_owner=True)  # BR-TASK-06.2

        now = datetime.now(timezone.utc)
        task.deleted_at = now
        task.updated_at = now
        self._task_repo.save(task)
        logger.info("task_deleted", extra={"task_id": task_id, "caller_id": caller_id})

    # ── Private helpers ───────────────────────────────────────────────────

    def _get_active_task(self, task_id: str) -> Task:
        task = self._task_repo.find_by_id(task_id)
        if task is None:
            raise NotFoundError(f"Task {task_id} not found")
        return task

    def _check_access(
        self, task: Task, caller_id: str, require_owner: bool = False
    ) -> None:
        if require_owner:
            if caller_id != task.owner_id:
                raise ForbiddenError("Only the task owner can perform this action")
        else:
            if caller_id not in (task.owner_id, task.assignee_id):
                raise ForbiddenError("Access denied")

    def _resolve_assignee(
        self, assignee_id: str | None, assignee_email: str | None
    ) -> str | None:
        if assignee_id is not None:
            user = self._user_repo.find_by_id(assignee_id)
            if user is None:
                raise NotFoundError(f"User {assignee_id} not found")
            return assignee_id
        if assignee_email is not None:
            user = self._user_repo.find_by_email(assignee_email)
            if user is None:
                raise NotFoundError(f"No user found with email {assignee_email}")
            return user.id
        return None

    def _apply_tag_merge(
        self,
        existing: list[str],
        to_add: list[str],
        to_remove: list[str],
    ) -> list[str]:
        after_remove = [t for t in existing if t not in to_remove]
        merged = after_remove + [t for t in to_add if t not in after_remove]
        return list(dict.fromkeys(merged))

    @staticmethod
    def _to_response(task: Task) -> TaskResponse:
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date,
            category=task.category,
            tags=task.tags,
            owner_id=task.owner_id,
            assignee_id=task.assignee_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

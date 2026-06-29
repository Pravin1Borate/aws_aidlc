from __future__ import annotations

from datetime import date

from src.core.storage import JsonFileStorage
from src.tasks.schemas import Task, TaskPriority, TaskStatus


class TaskRepository:
    def __init__(self, storage: JsonFileStorage) -> None:
        self._storage = storage

    def find_by_id(self, task_id: str) -> Task | None:
        record = self._storage.find_by_id(task_id)
        if record is None:
            return None
        task = Task.model_validate(record)
        if task.deleted_at is not None:
            return None
        return task

    def find_filtered(
        self,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        due_date_filter: date | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]:
        all_records = self._storage.read_all()
        tasks = [Task.model_validate(r) for r in all_records]

        # Active tasks only
        tasks = [t for t in tasks if t.deleted_at is None]

        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        if priority is not None:
            tasks = [t for t in tasks if t.priority == priority]
        if due_date_filter is not None:
            tasks = [
                t for t in tasks if t.due_date is not None and t.due_date <= due_date_filter
            ]

        # Sort by due_date ASC; tasks with no due_date sort last
        tasks.sort(key=lambda t: (t.due_date is None, t.due_date or date.min))

        total = len(tasks)
        return tasks[offset : offset + limit], total

    def save(self, task: Task) -> Task:
        self._storage.upsert(task.model_dump(mode="json"))
        return task

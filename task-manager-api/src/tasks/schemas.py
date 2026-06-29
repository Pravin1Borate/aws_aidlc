from __future__ import annotations

import enum
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


def _check_tags(tags: list[str]) -> list[str]:
    for tag in tags:
        if len(tag) > 50:
            raise ValueError(f"Tag '{tag}' exceeds 50 characters")
    return list(dict.fromkeys(tags))


class Task(BaseModel):
    """Internal domain model — includes all fields, never returned directly to clients."""

    id: str
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    due_date: date | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    owner_id: str
    assignee_id: str | None = None
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    due_date: date | None = None
    category: str | None = Field(None, max_length=100)
    tags: list[str] = Field(default_factory=list)
    assignee_id: str | None = None
    assignee_email: str | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        return _check_tags(v)


class TaskUpdate(BaseModel):
    """Full replacement semantics — omitted optional fields reset to None/default."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    due_date: date | None = None
    category: str | None = Field(None, max_length=100)
    tags: list[str] = Field(default_factory=list)
    assignee_id: str | None = None
    assignee_email: str | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        return _check_tags(v)


class TaskPatch(BaseModel):
    """Partial update — only fields in model_fields_set are applied."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    category: str | None = Field(None, max_length=100)
    tags: list[str] | None = None
    tags_remove: list[str] | None = None
    assignee_id: str | None = None
    assignee_email: str | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        return _check_tags(v)


class TaskResponse(BaseModel):
    """Public API response — never includes deleted_at (BR-TASK-02.3)."""

    id: str
    title: str
    description: str | None = None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None = None
    category: str | None = None
    tags: list[str]
    owner_id: str
    assignee_id: str | None = None
    created_at: datetime
    updated_at: datetime


class TaskFilter:
    """Query parameter container — not persisted."""

    def __init__(
        self,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        due_date: date | None = None,
    ) -> None:
        self.status = status
        self.priority = priority
        self.due_date = due_date

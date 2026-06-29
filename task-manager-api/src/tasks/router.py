from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response

from src.auth.schemas import UserResponse
from src.core.rate_limiter import limiter
from src.core.schemas import PaginatedResponse
from src.dependencies import get_current_user, get_task_service
from src.tasks.schemas import (
    TaskCreate,
    TaskFilter,
    TaskPatch,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)
from src.tasks.service import TaskService

task_router = APIRouter(prefix="/tasks", tags=["tasks"])


@task_router.get("/", response_model=PaginatedResponse[TaskResponse])
@limiter.limit("100/minute")
async def list_tasks(
    request: Request,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    due_date: date | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    task_service: TaskService = Depends(get_task_service),
    current_user: UserResponse = Depends(get_current_user),
) -> PaginatedResponse[TaskResponse]:
    filters = TaskFilter(status=status, priority=priority, due_date=due_date)
    items, total = task_service.list_tasks(filters, limit, offset)
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@task_router.post("/", response_model=TaskResponse, status_code=201)
@limiter.limit("100/minute")
async def create_task(
    request: Request,
    data: TaskCreate,
    task_service: TaskService = Depends(get_task_service),
    current_user: UserResponse = Depends(get_current_user),
) -> TaskResponse:
    return task_service.create(data, caller_id=str(current_user.id))


@task_router.get("/{task_id}", response_model=TaskResponse)
@limiter.limit("100/minute")
async def get_task(
    request: Request,
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
    current_user: UserResponse = Depends(get_current_user),
) -> TaskResponse:
    return task_service.get_by_id(task_id, caller_id=str(current_user.id))


@task_router.put("/{task_id}", response_model=TaskResponse)
@limiter.limit("100/minute")
async def update_task(
    request: Request,
    task_id: str,
    data: TaskUpdate,
    task_service: TaskService = Depends(get_task_service),
    current_user: UserResponse = Depends(get_current_user),
) -> TaskResponse:
    return task_service.full_update(task_id, data, caller_id=str(current_user.id))


@task_router.patch("/{task_id}", response_model=TaskResponse)
@limiter.limit("100/minute")
async def patch_task(
    request: Request,
    task_id: str,
    data: TaskPatch,
    task_service: TaskService = Depends(get_task_service),
    current_user: UserResponse = Depends(get_current_user),
) -> TaskResponse:
    return task_service.partial_update(task_id, data, caller_id=str(current_user.id))


@task_router.delete("/{task_id}", status_code=204)
@limiter.limit("100/minute")
async def delete_task(
    request: Request,
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
    current_user: UserResponse = Depends(get_current_user),
) -> Response:
    task_service.delete(task_id, caller_id=str(current_user.id))
    return Response(status_code=204)

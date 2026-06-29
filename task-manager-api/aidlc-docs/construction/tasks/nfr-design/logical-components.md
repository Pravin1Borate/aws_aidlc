# Logical Components — Unit 2: Task Management

## Updated Middleware Stack (main.py additions)

Unit 2 adds two routers to the existing app. Middleware stack unchanged.

```
[Existing Unit 1 middleware stack]
        |
        +---> /auth/*    → auth_router      (Unit 1)
        +---> /health/*  → health_router    (Unit 1)
        +---> /tasks/*   → task_router      (Unit 2 — NEW)
        +---> /users/*   → user_router      (Unit 2 — NEW)
```

---

## Component: TaskRouter

**File**: `src/tasks/router.py`
**Prefix**: `/tasks`
**Tag**: `tasks`

| Method | Path | Rate Limit | Auth | Handler |
|---|---|---|---|---|
| GET | `/` | 100/min | Yes | `list_tasks` |
| POST | `/` | 100/min | Yes | `create_task` |
| GET | `/{task_id}` | 100/min | Yes | `get_task` |
| PUT | `/{task_id}` | 100/min | Yes | `update_task` |
| PATCH | `/{task_id}` | 100/min | Yes | `patch_task` |
| DELETE | `/{task_id}` | 100/min | Yes | `delete_task` |

**Query params for `list_tasks`**:
- `status: TaskStatus | None`
- `priority: TaskPriority | None`
- `due_date: date | None`
- `limit: int = Query(100, ge=1, le=500)`
- `offset: int = Query(0, ge=0)`

---

## Component: TaskService

**File**: `src/tasks/service.py`

**Dependencies**: `TaskRepository`, `UserReadRepository`

```python
class TaskService:
    def create(self, data: TaskCreate, caller_id: str) -> TaskResponse
    def get_by_id(self, task_id: str, caller_id: str) -> TaskResponse
    def list_tasks(self, filters: TaskFilter, limit: int, offset: int) -> tuple[list[TaskResponse], int]
    def full_update(self, task_id: str, data: TaskUpdate, caller_id: str) -> TaskResponse
    def partial_update(self, task_id: str, data: TaskPatch, caller_id: str) -> TaskResponse
    def delete(self, task_id: str, caller_id: str) -> None

    # Private helpers
    def _get_active_task(self, task_id: str) -> Task          # raises NotFoundError if missing/deleted
    def _check_access(self, task: Task, caller_id: str, require_owner: bool = False) -> None
    def _resolve_assignee(self, assignee_id: str | None, assignee_email: str | None) -> str | None
    def _apply_tag_merge(self, existing, to_add, to_remove) -> list[str]
```

---

## Component: TaskRepository

**File**: `src/tasks/repository.py`

**Dependencies**: `JsonFileStorage`

```python
class TaskRepository:
    def find_by_id(self, task_id: str) -> Task | None
        # Returns None if not found OR deleted_at is not None

    def find_filtered(
        self,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        due_date: date | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]
        # Returns (page, total). Filters active only. Sorts by due_date ASC nulls-last.

    def save(self, task: Task) -> Task
        # Upsert via JsonFileStorage
```

---

## Component: UserRouter

**File**: `src/users/router.py`
**Prefix**: `/users`
**Tag**: `users`

| Method | Path | Rate Limit | Auth | Handler |
|---|---|---|---|---|
| GET | `/` | 100/min | Yes | `list_users` |
| GET | `/{user_id}` | 100/min | Yes | `get_user` |

---

## Component: UserService

**File**: `src/users/service.py`

**Dependencies**: `UserReadRepository`

```python
class UserService:
    def list_users(self) -> list[UserSummary]
    def get_by_id(self, user_id: str) -> UserSummary  # raises NotFoundError if missing
```

---

## Component: UserReadRepository

**File**: `src/users/repository.py`

**Dependencies**: `JsonFileStorage` (reads `users.json` — same path as Unit 1's `UserRepository`)

```python
class UserReadRepository:
    def find_all(self) -> list[UserSummary]
    def find_by_id(self, user_id: str) -> UserSummary | None
    def find_by_email(self, email: str) -> UserSummary | None

    # Private
    def _to_summary(self, record: dict) -> UserSummary
        # Maps raw dict → UserSummary, never exposing password_hash
```

**No write methods** — enforces read-only contract.

---

## New Shared Schema

**File**: `src/core/schemas.py` (new)

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
```

---

## Updated `src/dependencies.py` additions

```python
from src.tasks.repository import TaskRepository
from src.tasks.service import TaskService
from src.users.repository import UserReadRepository
from src.users.service import UserService

def get_task_repository() -> TaskRepository:
    storage = JsonFileStorage(f"{settings.DATA_DIR}/tasks.json")
    return TaskRepository(storage)

def get_user_read_repository() -> UserReadRepository:
    storage = JsonFileStorage(f"{settings.DATA_DIR}/users.json")
    return UserReadRepository(storage)

def get_task_service(
    task_repo: TaskRepository = Depends(get_task_repository),
    user_read_repo: UserReadRepository = Depends(get_user_read_repository),
) -> TaskService:
    return TaskService(task_repo, user_read_repo)

def get_user_service(
    user_read_repo: UserReadRepository = Depends(get_user_read_repository),
) -> UserService:
    return UserService(user_read_repo)
```

---

## Data Flow: Create Task (End-to-End)

```
POST /tasks { title, priority, assignee_email }
  → CorrelationIdMiddleware: generate correlation_id
  → slowapi: check rate limit (100/min, authenticated user)
  → get_current_user dependency: validate JWT → UserResponse(caller)
  → task_router.create_task(request, data=TaskCreate, task_service, current_user)
      → TaskService.create(data, caller_id=current_user.id)
          → _resolve_assignee(None, "alice@example.com")
              → UserReadRepository.find_by_email("alice@example.com") → UserSummary
              → returns alice.id
          → build Task entity (owner_id=caller.id, assignee_id=alice.id, ...)
          → TaskRepository.save(task)
          → return TaskResponse
  → 201 Created + X-Correlation-ID header
```

---

## Data Flow: List Tasks with Pagination (End-to-End)

```
GET /tasks?status=todo&limit=10&offset=0
  → get_current_user: validate JWT
  → task_router.list_tasks(request, status=todo, priority=None, due_date=None, limit=10, offset=0)
      → TaskService.list_tasks(filters, limit=10, offset=0)
          → TaskRepository.find_filtered(status=todo, priority=None, due_date=None, 10, 0)
              → load all tasks.json
              → filter: deleted_at is None, status == todo
              → total = len(filtered)     # e.g., 47
              → sort by due_date ASC nulls-last
              → slice [0:10]
              → return ([10 tasks], 47)
          → map to TaskResponse list
          → return ([10 TaskResponse], 47)
      → PaginatedResponse(items=[...], total=47, limit=10, offset=0)
  → 200 OK
```

# Tech Stack Decisions — Unit 2: Task Management

## No New Runtime Dependencies

All libraries already locked in Unit 1 `requirements.txt`:
- FastAPI, uvicorn, pydantic, pydantic-settings — runtime
- bcrypt, python-jose, slowapi — auth/security (already installed)
- python-json-logger — logging (already installed)

**No additions to `requirements.txt` or `requirements-dev.txt` needed.**

---

## New Architectural Patterns (Unit 2 specific)

### Pagination Response Envelope

```python
# src/core/schemas.py  (new shared module)
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
```

Query parameters for paginated endpoints:
```python
# Via FastAPI Query()
limit: int = Query(default=100, ge=1, le=500)
offset: int = Query(default=0, ge=0)
```

---

### UserReadRepository (Q2=B)

**File**: `src/users/repository.py`

```python
class UserReadRepository:
    def __init__(self, storage: JsonFileStorage) -> None: ...
    def find_all(self) -> list[UserSummary]: ...
    def find_by_id(self, user_id: str) -> UserSummary | None: ...
    def find_by_email(self, email: str) -> UserSummary | None: ...
```

- Read-only — no `save()`, `delete()`, or write methods
- Reads from the SAME `users.json` path as `UserRepository` (Unit 1)
- Returns `UserSummary` projections (id, email, full_name) — never exposes password_hash

---

### TaskRepository with filter support (Q3=B)

**File**: `src/tasks/repository.py`

```python
class TaskRepository:
    def find_by_id(self, task_id: str) -> Task | None:
        # Returns task only if deleted_at is None

    def find_filtered(
        self,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        due_date: date | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]:
        # Returns (page_of_tasks, total_count)
        # Filters: deleted_at is None, then status/priority/due_date ANDed
        # Sorts: due_date ASC nulls-last
        # Slices: [offset : offset+limit] AFTER counting total

    def save(self, task: Task) -> Task:
        # Upsert via JsonFileStorage

    def delete(self, task_id: str) -> bool:
        # Soft delete: load task, set deleted_at=now, save
        # Returns False if not found or already deleted
```

---

### New Source Packages (Unit 2)

```
src/
├── tasks/
│   ├── __init__.py
│   ├── router.py        — TaskRouter (/tasks)
│   ├── service.py       — TaskService
│   ├── repository.py    — TaskRepository with find_filtered
│   └── schemas.py       — Task, TaskCreate, TaskUpdate, TaskPatch, TaskResponse
├── users/
│   ├── __init__.py
│   ├── router.py        — UserRouter (/users)
│   ├── service.py       — UserService
│   └── repository.py    — UserReadRepository (read-only)
└── core/
    └── schemas.py       — PaginatedResponse[T] (new shared schema)
```

---

### Updated `src/main.py`

Unit 2 adds two new routers to the existing app:
```python
from src.tasks.router import task_router
from src.users.router import user_router

app.include_router(task_router)   # prefix=/tasks
app.include_router(user_router)   # prefix=/users
```

No other changes to main.py.

---

### Updated `src/dependencies.py`

Add factory functions for Unit 2:
```python
def get_task_repository() -> TaskRepository: ...
def get_task_service(...) -> TaskService: ...
def get_user_read_repository() -> UserReadRepository: ...
def get_user_service(...) -> UserService: ...
```

---

### Updated `/health/ready` check

`readiness` in `src/core/health.py` gains a `tasks_dir` check (Unit 2 adds `tasks.json` to data dir):
```python
checks = {
    "jwt_config": bool(settings.JWT_SECRET_KEY),
    "data_dir": data_dir_ok,
}
```
The existing `data_dir` check already covers `tasks.json` since both share `DATA_DIR`. No change needed.

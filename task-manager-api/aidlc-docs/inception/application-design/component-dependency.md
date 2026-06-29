# Component Dependencies

## Dependency Matrix

| Component | Depends On | Direction |
|---|---|---|
| `main.py` | AuthRouter, TaskRouter, UserRouter, RateLimiterMiddleware, ErrorHandlers, Settings | Assembles all |
| `dependencies.py` | AuthService, SecurityUtils | Provides DI factories |
| **auth/** | | |
| AuthRouter | AuthService, Pydantic models | Router → Service |
| AuthService | UserRepository, SecurityUtils | Service → Repo + Core |
| UserRepository | JsonFileStorage, Settings (DATA_DIR) | Repo → Core |
| **tasks/** | | |
| TaskRouter | TaskService, `get_current_user`, Pydantic models | Router → Service |
| TaskService | TaskRepository, UserRepository | Service → Repos |
| TaskRepository | JsonFileStorage, Settings (DATA_DIR) | Repo → Core |
| **users/** | | |
| UserRouter | UserService, `get_current_user`, Pydantic models | Router → Service |
| UserService | UserRepository | Service → Repo |
| **core/** | | |
| JsonFileStorage | `pathlib.Path`, `json`, `tempfile` (stdlib only) | No internal deps |
| SecurityUtils | `passlib`, `python-jose`, Settings | Core utils |
| RateLimiterMiddleware | `starlette.middleware`, Settings | Middleware |
| ErrorHandlers | `fastapi`, AppException classes | Core utils |
| Settings | `pydantic-settings` | Config |

---

## Dependency Graph

```
main.py
  ├── RateLimiterMiddleware (core)
  ├── ErrorHandlers (core)
  ├── AuthRouter (auth)
  │     └── AuthService
  │           ├── UserRepository
  │           │     └── JsonFileStorage (core)
  │           └── SecurityUtils (core)
  ├── TaskRouter (tasks)
  │     ├── get_current_user (dependencies.py)
  │     │     └── AuthService (shared instance)
  │     └── TaskService
  │           ├── TaskRepository
  │           │     └── JsonFileStorage (core)
  │           └── UserRepository (shared instance)
  └── UserRouter (users)
        ├── get_current_user (dependencies.py)
        └── UserService
              └── UserRepository (shared instance)
```

---

## Key Design Decisions

### Shared UserRepository
`UserRepository` is shared across `AuthService`, `TaskService`, and `UserService`. A single instance is created at startup and injected via FastAPI dependency factories in `dependencies.py`. This ensures all components read from the same data file handle.

### No Circular Dependencies
- Feature packages (`auth/`, `tasks/`, `users/`) depend only on `core/` — never on each other's services
- `core/` has no dependencies on any feature package
- Cross-feature data access (TaskService needing user data) uses the shared `UserRepository`, not `UserService`

### Middleware Ordering in `main.py`
```
Request → RateLimiterMiddleware → Route handler → ErrorHandlers → Response
```
Rate limiting runs before route handlers so it can reject requests before any business logic executes.

---

## Data Flow Diagrams

### Authentication Flow
```
POST /auth/login
  → AuthRouter (parse LoginRequest)
    → AuthService.login()
      → UserRepository.find_by_email()
        → JsonFileStorage.read_all()
      → SecurityUtils.verify_password()
      → SecurityUtils.create_access_token()
  ← AuthRouter (return TokenResponse)
```

### Task Creation Flow
```
POST /tasks
  → RateLimiterMiddleware (check limit)
  → TaskRouter (parse TaskCreate, call get_current_user)
    → get_current_user()
      → SecurityUtils.decode_access_token()
      → SecurityUtils.is_token_blacklisted()
      → UserRepository.find_by_id()
    → TaskService.create(data, owner_id)
      → [optional] UserRepository.find_by_id(assignee_id)
      → TaskRepository.save(new_task)
        → JsonFileStorage.upsert()
  ← TaskRouter (return TaskResponse 201)
```

### Task List with Filters Flow
```
GET /tasks?status=todo&priority=high
  → TaskRouter (parse query params, call get_current_user)
    → TaskService.list_accessible(caller_id, status, priority, due_date)
      → TaskRepository.find_accessible(caller_id)
        → JsonFileStorage.read_all()
      → [filter in-memory by status, priority, due_date]
      → [sort by due_date asc, nulls last]
  ← TaskRouter (return list[TaskResponse])
```

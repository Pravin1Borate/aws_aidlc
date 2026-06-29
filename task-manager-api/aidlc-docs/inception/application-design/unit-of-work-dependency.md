# Unit of Work Dependencies

## Development Sequence

```
Unit 1: Authentication  ──────────────────►  Unit 2: Task Management
  (auth/, core/security,                        (tasks/, users/,
   core/errors, core/logging,                    core/storage,
   config, dependencies, main)                   core/rate_limiter)
```

**Sequence**: Sequential. Unit 1 must be fully implemented, tested, and verified before Unit 2 begins.

---

## Dependency Matrix

| Dependency | From Unit | To Unit | Type | Reason |
|---|---|---|---|---|
| `get_current_user` dependency | Unit 2 | Unit 1 | Hard — compile-time | All Unit 2 routes require JWT auth via this dependency |
| `UserRepository` | Unit 2 | Unit 1 | Hard — runtime | `TaskService` needs `UserRepository.find_by_id()` to validate assignees |
| `AppException` hierarchy | Unit 2 | Unit 1 | Hard — import | Unit 2 services raise `NotFoundError`, `ForbiddenError` from `core/errors.py` |
| `StructuredLogger` | Unit 2 | Unit 1 | Soft — logging | Unit 2 components use `get_logger()` from `core/logging.py` |
| `Settings` | Unit 2 | Unit 1 | Hard — config | Unit 2 reads `DATA_DIR`, `RATE_LIMIT_*` from `config.py` |
| `main.py` wiring | Unit 2 | Unit 1 | Hard — assembly | Unit 2 routers are registered in `main.py` (created in Unit 1) |

---

## Shared Components

Components created in Unit 1 that Unit 2 reuses without modification:

| Component | Created in | Used by | Notes |
|---|---|---|---|
| `get_current_user` | Unit 1 (`dependencies.py`) | Unit 2 (all protected routes) | Inject via `Depends(get_current_user)` |
| `UserRepository` | Unit 1 (`auth/repository.py`) | Unit 2 (`TaskService`) | Inject via `Depends(get_user_repository)` factory |
| `AppException` subclasses | Unit 1 (`core/errors.py`) | Unit 2 services | Import directly |
| `StructuredLogger` | Unit 1 (`core/logging.py`) | Unit 2 all components | `get_logger(__name__)` |
| `Settings` singleton | Unit 1 (`config.py`) | Unit 2 all components | `from config import settings` |
| Global error handlers | Unit 1 (`core/errors.py`) | Unit 2 (automatic) | Registered on `app` in `main.py` |
| `RateLimiterMiddleware` registration | Unit 2 adds to `main.py` | All routes | Unit 2 adds middleware to existing `main.py` |

---

## Integration Points

### Unit 1 → Unit 2 Interface Contract

Unit 1 exposes these stable interfaces that Unit 2 must not break:

1. **`get_current_user(token) → UserResponse`** — must return `UserResponse` with at minimum: `id: UUID`, `email: str`, `full_name: str | None`
2. **`UserRepository.find_by_id(user_id) → User | None`** — must accept `UUID`, return `User` or `None`
3. **`UserRepository.list_all() → list[User]`** — must return all users
4. **`AppException(status_code, message)`** — constructor signature must remain stable
5. **`Settings.DATA_DIR`** — must be a valid `Path`; `tasks.json` will be written here

### Unit 2 Additions to `main.py`

Unit 2 adds to the existing `main.py` (created in Unit 1):
- Register `TaskRouter` (`app.include_router(task_router, prefix="/tasks")`)
- Register `UserRouter` (`app.include_router(user_router, prefix="/users")`)
- Add `RateLimiterMiddleware` (`app.add_middleware(RateLimiterMiddleware, ...)`)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Unit 1 UserRepository interface changes after Unit 2 starts | Low | High | Lock interface contract before starting Unit 2 |
| Token blacklist not persisted (in-memory) across restarts | Known design choice | Accepted | Documented in constraints; local dev only |
| JSON file concurrent write conflicts | Low (single-process) | Low | Atomic write (write-to-temp → rename) in `JsonFileStorage` |

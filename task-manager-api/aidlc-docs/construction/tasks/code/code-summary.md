# Code Summary — Unit 2: Task Management

## Files Created

### Source — New Packages

| File | Purpose |
|---|---|
| `src/tasks/__init__.py` | Package marker |
| `src/users/__init__.py` | Package marker |
| `src/core/schemas.py` | `PaginatedResponse[T]` generic (shared) |
| `src/tasks/schemas.py` | `TaskStatus`, `TaskPriority`, `Task`, `TaskCreate`, `TaskUpdate`, `TaskPatch`, `TaskResponse`, `TaskFilter` |
| `src/tasks/repository.py` | `TaskRepository` — `find_by_id`, `find_filtered` (paginated + sorted), `save` |
| `src/tasks/service.py` | `TaskService` — `create`, `get_by_id`, `list_tasks`, `full_update`, `partial_update`, `delete` + private helpers |
| `src/tasks/router.py` | `task_router` — 6 endpoints, all rate-limited 100/min, all authenticated |
| `src/users/schemas.py` | `UserSummary` — id, email, full_name (no password_hash) |
| `src/users/repository.py` | `UserReadRepository` — read-only, `find_all`, `find_by_id`, `find_by_email` |
| `src/users/service.py` | `UserService` — `list_users`, `get_by_id` |
| `src/users/router.py` | `user_router` — 2 endpoints, rate-limited, authenticated |

### Source — Modified

| File | Change |
|---|---|
| `src/dependencies.py` | Added `get_task_repository`, `get_user_read_repository`, `get_task_service`, `get_user_service` |
| `src/main.py` | Added imports + `app.include_router(task_router)` + `app.include_router(user_router)` |

### Tests

| File | Type | Count |
|---|---|---|
| `tests/unit/tasks/test_task_repository.py` | Unit | 12 tests |
| `tests/unit/tasks/test_task_service.py` | Unit | 20 tests |
| `tests/unit/users/test_user_service.py` | Unit | 5 tests |
| `tests/integration/tasks/test_task_endpoints.py` | Integration | 20 tests |
| `tests/integration/tasks/test_user_endpoints.py` | Integration | 7 tests |
| `tests/pbt/tasks/test_task_properties.py` | Property-Based | 7 Hypothesis properties |

**Total new tests**: ~71

---

## Story Traceability

| Story | Implemented |
|---|---|
| US-05 Create task | `TaskService.create`, `POST /tasks` |
| US-06 View task | `TaskService.get_by_id`, `GET /tasks/{id}` |
| US-07 Update task | `TaskService.full_update` + `partial_update`, `PUT /tasks/{id}` + `PATCH` |
| US-08 Delete task | `TaskService.delete`, `DELETE /tasks/{id}` (soft delete) |
| US-09 Set priority | `TaskPriority` enum, `TaskCreate`/`TaskUpdate` fields |
| US-10 Set due date | `due_date: date | None` field, filter support |
| US-11 Add categories | `category: str | None` field |
| US-12 Add tags | `tags: list[str]`, `_apply_tag_merge` (merge semantics) |
| US-13 Assign to user | `_resolve_assignee` (dual-format: id or email) |
| US-14 View assigned tasks | `BR-TASK-03.1`: all active tasks visible to any authenticated user |
| US-15 Accept assignment | `_check_access` grants assignee write access |
| US-16 Reassign | `BR-TASK-04.4`/`BR-TASK-05.5`: only owner can change assignee |
| US-17 Filter by status | `find_filtered(status=...)`, `?status=` query param |
| US-18 Filter by priority | `find_filtered(priority=...)`, `?priority=` query param |
| US-19 Filter by due date | `find_filtered(due_date_filter=...)`, `?due_date=` query param |
| US-20 Paginated list | `PaginatedResponse[T]`, `limit`/`offset` params |
| US-21 View any task | `BR-TASK-02.2`: any authenticated user can read any active task |
| US-22 List all users | `UserReadRepository`, `UserService`, `GET /users` + `GET /users/{id}` |

---

## Security Compliance Summary

| Rule | Status | Notes |
|---|---|---|
| SECURITY-08 (Object-level access) | Compliant | `_check_access(task, caller_id)` on every mutation |
| SECURITY-11 (Rate limiting) | Compliant | `@limiter.limit("100/minute")` on all 8 new endpoints |
| SECURITY-05 (Input validation) | Compliant | Pydantic field_validator, length constraints, enum validation |
| SECURITY-09 (Hardening) | Compliant | Generic 403 messages; `deleted_at` never in responses |
| SECURITY-03 (Structured logging) | Compliant | `task_id`, `caller_id`, action logged on every mutation |
| SECURITY-12 (Breached passwords) | Non-compliant | Known gap from Unit 1 — local dev PoC scope |

---

## Key Design Decisions Applied

| Decision | Implementation |
|---|---|
| Soft delete (Q3=B) | `deleted_at` field; `find_by_id` returns None if set; `deleted_at` filtered in `find_filtered` |
| Dual assignee format (Q4=C) | `_resolve_assignee(id, email)` — id takes precedence |
| Tag merge semantics (Q5=B) | `_apply_tag_merge(existing, to_add, to_remove)` — remove first, then add |
| All tasks visible (Q2=B) | Any authenticated user can read/list any active task |
| Past due dates accepted (Q1=A) | No validation on `due_date` being in the future |
| Pagination (BR-TASK-03) | `PaginatedResponse[T]`, limit default 100 max 500, offset 0 |
| Sort order | `due_date ASC nulls-last` — tasks without due_date appear last |

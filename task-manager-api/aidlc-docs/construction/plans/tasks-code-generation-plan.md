# Code Generation Plan — Unit 2: Task Management

## Unit Context

**Unit**: Task Management  
**Stories**: US-05 – US-22 (18 stories across 4 epics)  
**Dependencies**: Unit 1: Authentication (UserRepository, AuthService, JWT, JsonFileStorage)

### Stories Covered

| Epic | Stories |
|---|---|
| Epic 2: Task CRUD | US-05 Create task, US-06 View task, US-07 Update task, US-08 Delete task |
| Epic 3: Task Organization | US-09 Set priority, US-10 Set due date, US-11 Add categories, US-12 Add tags |
| Epic 4: Task Assignment | US-13 Assign to user, US-14 View assigned tasks, US-15 Accept assignment, US-16 Reassign |
| Epic 5: Task Search | US-17 Filter by status, US-18 Filter by priority, US-19 Filter by due date, US-20 Paginated list, US-21 View any task, US-22 List all users |

### Architecture Pattern
Three-tier per feature: Router → Service → Repository  
Shared: `PaginatedResponse[T]` in `src/core/schemas.py`  
Read-only user access: `UserReadRepository` in `src/users/repository.py` (reads same `users.json` as Unit 1, never writes)

---

## Plan Execution Checklist

### Section A: Package Scaffolding

- [x] **Step 1**: Create `src/tasks/__init__.py`
- [x] **Step 2**: Create `src/users/__init__.py`
- [x] **Step 3**: Create `tests/unit/tasks/__init__.py`
- [x] **Step 4**: Create `tests/unit/users/__init__.py`
- [x] **Step 5**: Create `tests/integration/tasks/__init__.py`
- [x] **Step 6**: Create `tests/pbt/tasks/__init__.py`

### Section B: Shared Core Schema

- [x] **Step 7**: Create `src/core/schemas.py`
  - `PaginatedResponse[T](BaseModel, Generic[T])` with `items`, `total`, `limit`, `offset`

### Section C: Users Domain Layer

- [x] **Step 8**: Create `src/users/schemas.py`
  - `UserSummary` — `id`, `email`, `full_name` (no `password_hash`)
- [x] **Step 9**: Create `src/users/repository.py`
  - `UserReadRepository(JsonFileStorage)` — `find_all`, `find_by_id`, `find_by_email`, `_to_summary`
  - **Read-only**: no write methods (BR-TASK-07.4 security invariant)
- [x] **Step 10**: Create `src/users/service.py`
  - `UserService(UserReadRepository)` — `list_users`, `get_by_id` (raises `NotFoundError` if missing)

### Section D: Task Domain Layer

- [x] **Step 11**: Create `src/tasks/schemas.py`
  - Enums: `TaskStatus` (todo/in_progress/done), `TaskPriority` (low/medium/high)
  - Internal model: `Task` (all 13 fields including `deleted_at`)
  - Input models: `TaskCreate`, `TaskUpdate`, `TaskPatch` (adds `tags_remove`)
  - Output model: `TaskResponse` (no `deleted_at` — BR-TASK-02.3)
  - Query object: `TaskFilter` (status, priority, due_date)
- [x] **Step 12**: Create `src/tasks/repository.py`
  - `TaskRepository(JsonFileStorage)`:
    - `find_by_id(task_id) -> Task | None` — returns `None` if missing OR `deleted_at is not None`
    - `find_filtered(status, priority, due_date, limit, offset) -> tuple[list[Task], int]` — active only, sorted by `due_date ASC nulls-last`, paginated
    - `save(task) -> Task` — upsert via `JsonFileStorage`
- [x] **Step 13**: Create `src/tasks/service.py`
  - `TaskService(TaskRepository, UserReadRepository)`:
    - `create(data, caller_id) -> TaskResponse` — BR-TASK-01 (all 12 sub-rules)
    - `get_by_id(task_id, caller_id) -> TaskResponse` — BR-TASK-02
    - `list_tasks(filters, limit, offset) -> tuple[list[TaskResponse], int]` — BR-TASK-03 (sorts, filters, paginates)
    - `full_update(task_id, data, caller_id) -> TaskResponse` — BR-TASK-04 (owner/assignee write access)
    - `partial_update(task_id, data, caller_id) -> TaskResponse` — BR-TASK-05 (tag merge, partial replace)
    - `delete(task_id, caller_id) -> None` — BR-TASK-06 (owner only, soft-delete)
    - `_get_active_task(task_id) -> Task` — raises `NotFoundError`
    - `_check_access(task, caller_id, require_owner=False) -> None` — raises `ForbiddenError`
    - `_resolve_assignee(assignee_id, assignee_email) -> str | None` — raises `NotFoundError`
    - `_apply_tag_merge(existing, to_add, to_remove) -> list[str]` — BR-TASK-05.6-7

### Section E: API Routers

- [x] **Step 14**: Create `src/tasks/router.py`
  - Prefix `/tasks`, tag `tasks`
  - All 6 endpoints with `@limiter.limit("100/minute")` (SECURITY-11)
  - All endpoints require `get_current_user` dependency (SECURITY-08)
  - `list_tasks`: query params `status`, `priority`, `due_date`, `limit=Query(100,ge=1,le=500)`, `offset=Query(0,ge=0)` → `PaginatedResponse[TaskResponse]`
  - `create_task`: returns 201, body `TaskCreate`
  - `get_task`, `update_task`, `patch_task`: 200 + `TaskResponse`
  - `delete_task`: 204, no body
- [x] **Step 15**: Create `src/users/router.py`
  - Prefix `/users`, tag `users`
  - `GET /` and `GET /{user_id}` with `@limiter.limit("100/minute")` + `get_current_user`
  - Returns `UserSummary` / `list[UserSummary]`

### Section F: Application Wiring

- [x] **Step 16**: Update `src/dependencies.py`
  - Add 4 factory functions: `get_task_repository`, `get_user_read_repository`, `get_task_service`, `get_user_service`
- [x] **Step 17**: Update `src/main.py`
  - Import `task_router` and `user_router`
  - Add `app.include_router(task_router)` and `app.include_router(user_router)`

### Section G: Unit Tests

- [x] **Step 18**: Create `tests/unit/tasks/test_task_repository.py`
  - Tests: find_by_id (found, not found, soft-deleted), find_filtered (no filters, by status, by priority, by due_date, pagination, sort order), save (create, update)
  - ~12 tests
- [x] **Step 19**: Create `tests/unit/tasks/test_task_service.py`
  - Tests: create (success, missing assignee), get_by_id (found, not found), list_tasks (no filters, with filters), full_update (owner ok, assignee ok, forbidden, immutable owner_id), partial_update (tag merge, partial replace, forbidden), delete (owner ok, assignee forbidden, not found)
  - ~18 tests
- [x] **Step 20**: Create `tests/unit/users/test_user_service.py`
  - Tests: list_users, get_by_id (found, not found)
  - ~5 tests

### Section H: Integration Tests

- [x] **Step 21**: Create `tests/integration/tasks/test_task_endpoints.py`
  - End-to-end tests via `TestClient` for all 6 task endpoints
  - Test auth enforcement (401 without token), rate limit wiring, CRUD flow, filter params, pagination response shape, soft-delete visibility, 403/404 scenarios
  - ~20 tests
- [x] **Step 22**: Create `tests/integration/tasks/test_user_endpoints.py`
  - End-to-end tests for `GET /users` and `GET /users/{id}`
  - Auth enforcement, list all, get by id, 404
  - ~6 tests

### Section I: Property-Based Tests

- [x] **Step 23**: Create `tests/pbt/tasks/test_task_properties.py`
  - PBT properties (Hypothesis):
    1. Tag deduplication is idempotent
    2. Tag merge order invariant (remove then add always correct)
    3. Soft-delete makes task invisible to get/list
    4. owner_id never changes after any update
    5. Pagination total is consistent with filtered count
    6. due_date filter never returns tasks with due_date > filter
    7. Full update sets all fields (no stale values from prior state)

### Section J: Code Documentation

- [x] **Step 24**: Create `aidlc-docs/construction/tasks/code/code-summary.md`
  - List all created files, story traceability table, security compliance summary

---

## Story Traceability

| Story | Implemented By |
|---|---|
| US-05 Create task | Step 13 (TaskService.create), Step 14 (POST /tasks), Step 19, Step 21 |
| US-06 View task | Step 13 (TaskService.get_by_id), Step 14 (GET /tasks/{id}), Step 19, Step 21 |
| US-07 Update task | Step 13 (full_update + partial_update), Step 14 (PUT + PATCH), Step 19, Step 21 |
| US-08 Delete task | Step 13 (TaskService.delete), Step 14 (DELETE /tasks/{id}), Step 19, Step 21 |
| US-09 Set priority | Step 11 (TaskPriority enum), Step 13 (create/update), Step 19 |
| US-10 Set due date | Step 11 (due_date field), Step 13 (create/update), Step 19 |
| US-11 Add categories | Step 11 (category field), Step 13 (create/update), Step 19 |
| US-12 Add tags | Step 11 (tags field), Step 13 (tag merge), Step 19, Step 23 |
| US-13 Assign to user | Step 13 (_resolve_assignee), Step 19 |
| US-14 View assigned tasks | Step 12 (find_filtered by assignee implicit via BR-TASK-03.1), Step 14 (list) |
| US-15 Accept assignment | Step 13 (assignee in access check), Step 19 |
| US-16 Reassign | Step 13 (BR-TASK-04.4/05.5 owner-only assignee change), Step 19 |
| US-17 Filter by status | Step 12 (find_filtered), Step 14 (query param), Step 21 |
| US-18 Filter by priority | Step 12 (find_filtered), Step 14 (query param), Step 21 |
| US-19 Filter by due date | Step 12 (find_filtered), Step 14 (query param), Step 21 |
| US-20 Paginated list | Step 7 (PaginatedResponse[T]), Step 12 (pagination), Step 14, Step 23 |
| US-21 View any task | Step 13 (BR-TASK-02.2 any auth user), Step 14, Step 21 |
| US-22 List all users | Steps 9-10, Step 15, Step 22 |

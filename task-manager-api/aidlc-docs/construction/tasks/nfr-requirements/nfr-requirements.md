# NFR Requirements — Unit 2: Task Management

## Performance

| ID | Requirement | Target | Rationale |
|---|---|---|---|
| PERF-TASK-01 | `GET /tasks` list (no filters) | < 200ms (P95) | Full JSON read + in-memory filter + sort |
| PERF-TASK-02 | `GET /tasks/{id}` | < 50ms (P95) | Linear scan of tasks.json |
| PERF-TASK-03 | `POST /tasks` | < 100ms (P95) | Atomic write to tasks.json + optional user lookup |
| PERF-TASK-04 | `PUT /tasks/{id}`, `PATCH /tasks/{id}` | < 150ms (P95) | Read + modify + atomic write + user lookup |
| PERF-TASK-05 | `DELETE /tasks/{id}` | < 100ms (P95) | Soft delete — read + atomic write |
| PERF-TASK-06 | `GET /users`, `GET /users/{id}` | < 50ms (P95) | Read users.json (typically small) |

**Note**: Performance targets are for local dev with ≤ 1000 tasks and ≤ 100 users in JSON files.

---

## Pagination

| ID | Requirement | Detail |
|---|---|---|
| PAGE-01 | `GET /tasks` supports optional `limit` and `offset` query params | Default: limit=100, offset=0 |
| PAGE-02 | Maximum `limit` value | 500 — reject with 422 if exceeded |
| PAGE-03 | Response envelope for `GET /tasks` | `{"items": [...], "total": N, "limit": N, "offset": N}` |
| PAGE-04 | `total` in response | Count of matching tasks BEFORE pagination (after filters, before slice) |

---

## Security

| ID | Requirement | Source Rule | Implementation |
|---|---|---|---|
| SEC-TASK-01 | Object-level access control on all mutations | SECURITY-08 | Owner/assignee check before every PUT/PATCH/DELETE |
| SEC-TASK-02 | Rate limiting on all task/user endpoints | SECURITY-11 | `@limiter.limit("100/minute")` on every route |
| SEC-TASK-03 | Input validation on all request bodies and query params | SECURITY-05 | Pydantic models + `Query()` validators |
| SEC-TASK-04 | No task internals leaked on auth/authz failure | SECURITY-09 | Generic 403/404 messages, no task data in error body |
| SEC-TASK-05 | Structured access logging per task mutation | SECURITY-03 | Log task_id, caller_id, action, outcome in every handler |
| SEC-TASK-06 | Deleted tasks return 404 (not 403) | SECURITY-09 | Treats deleted as non-existent — no information leak |

---

## Reliability

| ID | Requirement | Detail |
|---|---|---|
| REL-TASK-01 | Atomic write for tasks.json | Inherited from `JsonFileStorage` — write-to-temp → os.replace() |
| REL-TASK-02 | Global exception handler catches unhandled errors | Inherited from `main.py` — 500 with generic message |
| REL-TASK-03 | Input validation errors return structured 422 | Pydantic v2 automatic |
| REL-TASK-04 | tasks.json directory auto-created on startup | `lifespan` creates DATA_DIR — already covers tasks subpath |

---

## Testability

| ID | Requirement | Detail |
|---|---|---|
| TEST-TASK-01 | Unit test coverage | pytest, minimum 80% line coverage on `tasks/`, `users/` |
| TEST-TASK-02 | Property-based tests | Hypothesis — 7 properties from business-logic-model.md |
| TEST-TASK-03 | Test isolation | All tests use `tmp_path` for tasks.json; no shared state |
| TEST-TASK-04 | Integration tests | All 8 task + 2 user endpoints covered end-to-end |
| TEST-TASK-05 | Pagination tests | Verify `total`, `items`, `limit`, `offset` in paginated responses |

---

## Architecture Decisions (Q2 and Q3)

### Q2: UserReadRepository (B — new read-only wrapper)

- **Location**: `src/users/repository.py`
- **Purpose**: Read-only access to `users.json` for assignee resolution and `/users` endpoints
- **Does NOT** write to `users.json` — that remains Unit 1's exclusive responsibility
- **Interface**: `find_all() -> list[UserSummary]`, `find_by_id(id) -> UserSummary | None`, `find_by_email(email) -> UserSummary | None`

### Q3: Filter logic in TaskRepository (B)

- **`find_filtered(status, priority, due_date, limit, offset)`** handles WHERE + SORT + SLICE
- Service layer receives already-filtered, paginated results and the total count
- **`find_by_id(task_id)`** returns single active task (deleted_at is None) or None
- **`save(task)`** creates or updates (via `JsonFileStorage.upsert()`)

---

## Extension Compliance Summary

### Security Baseline
| Rule | Status | Notes |
|---|---|---|
| SECURITY-08 (Object-level access) | Compliant | Owner/assignee verified on every mutation |
| SECURITY-05 (Input validation) | Compliant | Pydantic + Query validators |
| SECURITY-11 (Rate limiting) | Compliant | @limiter.limit("100/minute") on all endpoints |
| SECURITY-09 (Hardening) | Compliant | Generic error messages; deleted tasks return 404 |
| SECURITY-03 (Structured logging) | Compliant | task_id + caller_id in every log entry |
| Others | N/A | Local dev scope |

### Resiliency Baseline
| Rule | Status | Notes |
|---|---|---|
| RESILIENCY-04 (Health checks) | Compliant | Inherited from Unit 1 — /health/ready checks DATA_DIR |
| Others | N/A | Local dev scope |

### Property-Based Testing
| Rule | Status | Notes |
|---|---|---|
| PBT-01 (Property identification) | Compliant | 7 properties identified in business-logic-model.md |
| PBT-02–04 (Round-trip, invariants, idempotence) | Compliant | All 3 categories covered across 7 properties |

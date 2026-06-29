# Business Rules — Unit 2: Task Management

## BR-TASK-01: Task Creation

| Rule ID | Rule | Error if violated |
|---|---|---|
| BR-TASK-01.1 | `title` is required and must be 1–255 characters | 422 Unprocessable Entity |
| BR-TASK-01.2 | `description` if provided must be ≤ 2000 characters | 422 Unprocessable Entity |
| BR-TASK-01.3 | `status` defaults to `todo`; if provided must be a valid TaskStatus value | 422 Unprocessable Entity |
| BR-TASK-01.4 | `priority` defaults to `medium`; if provided must be a valid TaskPriority value | 422 Unprocessable Entity |
| BR-TASK-01.5 | `due_date` if provided must be a valid ISO 8601 date (YYYY-MM-DD); past dates accepted silently | 422 if format invalid |
| BR-TASK-01.6 | `category` if provided must be ≤ 100 characters | 422 Unprocessable Entity |
| BR-TASK-01.7 | Each tag in `tags` must be ≤ 50 characters; exact duplicates removed before storage | 422 if any tag exceeds 50 chars |
| BR-TASK-01.8 | `owner_id` is set to the authenticated caller's UUID — client cannot supply it | — (processing rule) |
| BR-TASK-01.9 | If `assignee_id` provided: verify user exists → 404 if not found | 404 Not Found |
| BR-TASK-01.10 | If `assignee_email` provided (and no `assignee_id`): resolve email to user → 404 if user not found | 404 Not Found |
| BR-TASK-01.11 | If both `assignee_id` and `assignee_email` provided: `assignee_id` takes precedence | — (processing rule) |
| BR-TASK-01.12 | `id`, `created_at`, `updated_at`, `deleted_at` are system-set — client cannot supply them | — (processing rule) |

---

## BR-TASK-02: Task Read by ID (GET /tasks/{id})

| Rule ID | Rule | Error if violated |
|---|---|---|
| BR-TASK-02.1 | Task must exist in storage and `deleted_at` must be `None` | 404 Not Found |
| BR-TASK-02.2 | Any authenticated user can read any active task (Q2=B — all tasks visible) | — |
| BR-TASK-02.3 | Response must never include `deleted_at` or internal storage fields | — (security invariant) |

---

## BR-TASK-03: Task List (GET /tasks)

| Rule ID | Rule | Error if violated |
|---|---|---|
| BR-TASK-03.1 | Returns all tasks where `deleted_at is None` (Q2=B — system-wide) | — |
| BR-TASK-03.2 | `status` filter: if provided, returns only tasks matching the given status | 422 if invalid enum value |
| BR-TASK-03.3 | `priority` filter: if provided, returns only tasks matching the given priority | 422 if invalid enum value |
| BR-TASK-03.4 | `due_date` filter: if provided, returns only tasks with `due_date ≤ filter_date` (tasks with no due date excluded from filtered results) | 422 if invalid date format |
| BR-TASK-03.5 | Results sorted by `due_date` ascending; tasks with no `due_date` appear last | — (processing rule) |
| BR-TASK-03.6 | Multiple filters are ANDed together | — (processing rule) |

---

## BR-TASK-04: Full Update (PUT /tasks/{id})

| Rule ID | Rule | Error if violated |
|---|---|---|
| BR-TASK-04.1 | Task must exist and `deleted_at` must be `None` | 404 Not Found |
| BR-TASK-04.2 | Caller must be `owner_id` OR `assignee_id` of the task | 403 Forbidden |
| BR-TASK-04.3 | `owner_id` is immutable — cannot be changed by any user | — (security invariant) |
| BR-TASK-04.4 | `assignee_id` can only be changed by the `owner_id`; assignee cannot reassign | 403 if assignee attempts to change assignee |
| BR-TASK-04.5 | All mutable fields are replaced with supplied values; omitted optional fields are set to `None`/default | — (full-replace semantics) |
| BR-TASK-04.6 | Same validation rules as BR-TASK-01 apply to all supplied fields | 422 Unprocessable Entity |
| BR-TASK-04.7 | `updated_at` is set to `utcnow()` | — (processing rule) |

---

## BR-TASK-05: Partial Update (PATCH /tasks/{id})

| Rule ID | Rule | Error if violated |
|---|---|---|
| BR-TASK-05.1 | Task must exist and `deleted_at` must be `None` | 404 Not Found |
| BR-TASK-05.2 | Caller must be `owner_id` OR `assignee_id` of the task | 403 Forbidden |
| BR-TASK-05.3 | Only fields present in the request body are modified; absent fields are unchanged | — (partial-replace semantics) |
| BR-TASK-05.4 | `owner_id` is immutable | — (security invariant) |
| BR-TASK-05.5 | `assignee_id` can only be changed by `owner_id` | 403 if assignee attempts to change assignee |
| BR-TASK-05.6 | **Tag merge** (Q5=B): `tags` in body are ADDED to existing tags (deduplicated); `tags_remove` in body removes specific tags by exact match | — (merge semantics) |
| BR-TASK-05.7 | `tags_remove` is applied BEFORE `tags` (remove first, then add) | — (processing rule) |
| BR-TASK-05.8 | Same field-level validation rules apply (length, enum values) | 422 Unprocessable Entity |
| BR-TASK-05.9 | `updated_at` is set to `utcnow()` | — (processing rule) |

---

## BR-TASK-06: Task Delete (DELETE /tasks/{id})

| Rule ID | Rule | Error if violated |
|---|---|---|
| BR-TASK-06.1 | Task must exist and `deleted_at` must be `None` | 404 Not Found |
| BR-TASK-06.2 | Only `owner_id` can delete (FR-06.4); assignee cannot | 403 Forbidden |
| BR-TASK-06.3 | **Soft delete** (Q3=B): set `deleted_at = utcnow()`, persist. Do NOT remove record. | — (processing rule) |
| BR-TASK-06.4 | Returns 204 No Content on success | — |
| BR-TASK-06.5 | Soft-deleted task is immediately invisible to all read/list/update operations | — (security invariant) |

---

## BR-TASK-07: User Operations (/users)

| Rule ID | Rule | Error if violated |
|---|---|---|
| BR-TASK-07.1 | `GET /users` returns all registered users (non-deleted) as UserSummary projections | — |
| BR-TASK-07.2 | `GET /users/{id}` returns a single UserSummary; 404 if user not found | 404 Not Found |
| BR-TASK-07.3 | Both endpoints require authentication | 401 Unauthorized |
| BR-TASK-07.4 | `password_hash`, `failed_login_attempts`, `lockout_until` are never included in UserSummary | — (security invariant) |

---

## Security Compliance Summary (SECURITY Extension)

| Rule | Status | Notes |
|---|---|---|
| SECURITY-08 (Object-level access control) | Compliant | Every task mutation verifies `owner_id`/`assignee_id` against caller |
| SECURITY-05 (Input validation) | Compliant | Pydantic validates all fields; enum values, length constraints, date formats |
| SECURITY-09 (Hardening) | Compliant | 403 generic message; no task internals leaked on auth failure |
| SECURITY-11 (Rate limiting) | Compliant | slowapi decorators on all task/user endpoints (100/min authenticated) |
| SECURITY-03 (Structured logging) | Compliant | task_id, caller_id, action logged on every mutation |
| Others | N/A | Local dev scope |

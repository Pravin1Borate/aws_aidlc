# NFR Design Patterns — Unit 2: Task Management

## Pattern 1: Object-Level Authorization (Security)

**Satisfies**: SEC-TASK-01, SECURITY-08, BR-TASK-04.2, BR-TASK-05.2, BR-TASK-06.2

**Pattern**: Every mutation checks caller identity against task fields before any business logic runs. Authorization is a synchronous guard method on `TaskService`, called at the top of each mutating workflow.

```
TaskService._check_access(task, caller_id, require_owner=False):
    if require_owner:
        if task.owner_id != caller_id: raise ForbiddenError
    else:
        if task.owner_id != caller_id AND task.assignee_id != caller_id:
            raise ForbiddenError

# Usage in service methods:
def full_update(self, task_id, data, caller_id):
    task = self._get_active_task(task_id)     # 404 if deleted or missing
    self._check_access(task, caller_id)        # 403 if not owner/assignee
    ...

def delete(self, task_id, caller_id):
    task = self._get_active_task(task_id)
    self._check_access(task, caller_id, require_owner=True)  # 403 if not owner
    ...
```

**Key constraint**: Deleted tasks return 404 (not 403) — authorization check never reached for deleted tasks.

---

## Pattern 2: Soft Delete Visibility Filter

**Satisfies**: BR-TASK-06.3, BR-TASK-06.5, SEC-TASK-06

**Pattern**: `deleted_at is not None` tasks are treated as non-existent at every access point. The filter lives in `TaskRepository`, not in the service, ensuring no deleted task ever surfaces regardless of the caller.

```
TaskRepository.find_by_id(task_id):
    record = storage.find_by_id(task_id)
    if record is None or record.get("deleted_at") is not None:
        return None   # caller gets 404

TaskRepository.find_filtered(...):
    all_records = storage.read_all()
    active = [r for r in all_records if r.get("deleted_at") is None]
    # ... then filter/sort/paginate over `active` only
```

---

## Pattern 3: Filter + Sort + Paginate in Repository

**Satisfies**: BR-TASK-03, PAGE-01–04

**Pattern**: `find_filtered()` executes the full data-access pipeline in a single method call. Service receives a `(items, total)` tuple — no knowledge of pagination mechanics.

```
find_filtered(status, priority, due_date, limit, offset) -> (list[Task], int):

  Step 1: Load all active (non-deleted) records
  Step 2: Apply filters (ANDed):
          status filter:    task.status == status  (if provided)
          priority filter:  task.priority == priority  (if provided)
          due_date filter:  task.due_date is not None AND task.due_date <= due_date  (if provided)
  Step 3: total = len(filtered)
  Step 4: Sort:
          key = (0 if task.due_date else 1, task.due_date or date.max)
          sorted ascending
  Step 5: Slice: items = filtered[offset : offset + limit]
  Step 6: Return (items, total)
```

---

## Pattern 4: Pagination Response Envelope

**Satisfies**: PAGE-01–04

**Pattern**: Generic `PaginatedResponse[T]` wraps all paginated list responses. Defined once in `src/core/schemas.py`, used by `TaskRouter` for `GET /tasks`.

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
```

Service returns `(items, total)`. Router constructs the envelope:
```python
items, total = task_service.list_tasks(filters, limit, offset)
return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
```

---

## Pattern 5: Assignee Resolution

**Satisfies**: BR-TASK-01.9–01.11, FR-06.1 (both ID and email)

**Pattern**: Dual-format resolution is a private method on `TaskService`. `assignee_id` takes precedence; email is resolved to UUID if no ID supplied.

```
TaskService._resolve_assignee(assignee_id, assignee_email) -> str | None:
    if assignee_id:
        user = user_read_repo.find_by_id(assignee_id)
        if user is None: raise NotFoundError("Assignee not found")
        return assignee_id
    if assignee_email:
        user = user_read_repo.find_by_email(assignee_email)
        if user is None: raise NotFoundError("Assignee not found")
        return user.id
    return None
```

Called identically from `create()`, `full_update()`, and `partial_update()`.

---

## Pattern 6: Tag Merge (PATCH semantics)

**Satisfies**: BR-TASK-05.6, BR-TASK-05.7

**Pattern**: Tags are merged in two phases — remove first, then add, then deduplicate.

```
TaskService._apply_tag_merge(existing_tags, tags_to_add, tags_to_remove) -> list[str]:
    # Phase 1: remove
    result = [t for t in existing_tags if t not in (tags_to_remove or [])]
    # Phase 2: add (append only new)
    for tag in (tags_to_add or []):
        if tag not in result:
            result.append(tag)
    return result
```

Called only from `partial_update()`. Full update (`full_update()`) replaces tags entirely.

---

## Pattern 7: UserSummary Projection

**Satisfies**: BR-TASK-07.4, SECURITY-08 (no sensitive data leakage)

**Pattern**: `UserReadRepository` always maps raw user records to `UserSummary` before returning. The `password_hash`, `failed_login_attempts`, and `lockout_until` fields are never accessible from Unit 2 code.

```
UserReadRepository._to_summary(record: dict) -> UserSummary:
    return UserSummary(
        id=record["id"],
        email=record["email"],
        full_name=record.get("full_name"),
    )
```

`UserReadRepository` has no `save()` method — enforces read-only contract at the class level.

---

## Extension Compliance Summary

| Rule | Pattern Applied | Status |
|---|---|---|
| SECURITY-08 (Object-level access) | Pattern 1 — `_check_access` guard | Compliant |
| SECURITY-05 (Input validation) | Pydantic models + Query validators | Compliant |
| SECURITY-11 (Rate limiting) | `@limiter.limit("100/minute")` on all routes | Compliant |
| SECURITY-09 (Hardening) | Pattern 2 — deleted tasks return 404 | Compliant |
| SECURITY-03 (Logging) | Inherited CorrelationIdMiddleware + task_id in logs | Compliant |
| PBT-01 (Properties identified) | 7 properties in business-logic-model.md | Compliant |

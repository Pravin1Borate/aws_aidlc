# Business Logic Model — Unit 2: Task Management

## Workflow 1: Create Task (POST /tasks)

```
Input: TaskCreate { title, description?, status?, priority?, due_date?,
                    category?, tags?, assignee_id?, assignee_email? }
Caller: authenticated user (owner)

1. Validate all fields (BR-TASK-01.1–01.8)
2. Resolve assignee (if provided):
   a. If assignee_id AND assignee_email both present → use assignee_id (ignore email)
   b. If only assignee_id → verify user exists in users.json → 404 if not found
   c. If only assignee_email → look up user by email → 404 if not found → resolve to UUID
   d. If neither → assignee_id = None
3. Deduplicate tags (exact match, preserve order of first occurrence)
4. Create Task entity:
   id           = uuid4()
   title        = data.title
   description  = data.description or None
   status       = data.status or TaskStatus.todo
   priority     = data.priority or TaskPriority.medium
   due_date     = data.due_date or None    # past dates accepted silently
   category     = data.category or None
   tags         = deduped tags list
   owner_id     = caller.id
   assignee_id  = resolved UUID or None
   deleted_at   = None
   created_at   = utcnow()
   updated_at   = utcnow()
5. Persist to tasks.json
6. Return TaskResponse (id, all fields except deleted_at, created_at, updated_at)
```

---

## Workflow 2: Get Task by ID (GET /tasks/{id})

```
Input: task_id (UUID string), caller: authenticated user

1. Look up task by task_id in tasks.json
2. If not found OR deleted_at is not None → raise NotFoundError (404)
3. Return TaskResponse
```

---

## Workflow 3: List Tasks (GET /tasks?status=&priority=&due_date=)

```
Input: filters { status?, priority?, due_date? }, caller: authenticated user

1. Load all tasks from tasks.json
2. Filter: retain only tasks where deleted_at is None
3. Apply filters (all ANDed):
   a. If status filter: retain tasks where task.status == filter.status
   b. If priority filter: retain tasks where task.priority == filter.priority
   c. If due_date filter: retain tasks where task.due_date is not None
                          AND task.due_date <= filter.due_date
4. Sort:
   - Tasks with due_date: sorted ascending by due_date
   - Tasks without due_date: appended after, in created_at order
5. Return list[TaskResponse]
```

---

## Workflow 4: Full Update (PUT /tasks/{id})

```
Input: task_id, TaskUpdate { title, description, status, priority, due_date,
                              category, tags, assignee_id?, assignee_email? }
Caller: authenticated user

1. Look up task → 404 if not found or deleted
2. Check authorization: caller.id == task.owner_id OR caller.id == task.assignee_id
   → 403 if neither
3. If caller is assignee (not owner) AND request changes assignee_id → 403
4. Resolve new assignee (same logic as Workflow 1 step 2)
5. Validate all fields (same as BR-TASK-01)
6. Replace ALL mutable fields:
   task.title       = data.title
   task.description = data.description      # None if omitted
   task.status      = data.status
   task.priority    = data.priority
   task.due_date    = data.due_date          # None if omitted
   task.category    = data.category          # None if omitted
   task.tags        = deduped(data.tags)     # [] if omitted
   task.assignee_id = resolved assignee or None
   task.updated_at  = utcnow()
   (task.owner_id and task.id are NOT updated)
7. Persist updated task
8. Return TaskResponse
```

---

## Workflow 5: Partial Update (PATCH /tasks/{id})

```
Input: task_id, TaskPatch { title?, description?, status?, priority?, due_date?,
                             category?, tags?, tags_remove?, assignee_id?, assignee_email? }
Caller: authenticated user

1. Look up task → 404 if not found or deleted
2. Check authorization: caller.id == task.owner_id OR caller.id == task.assignee_id
   → 403 if neither
3. If caller is assignee AND request includes assignee_id/assignee_email → 403
4. For each present field in request, apply update:
   - title       → replace if present
   - description → replace if present (can be set to null explicitly)
   - status      → replace if present
   - priority    → replace if present
   - due_date    → replace if present (can be set to null)
   - category    → replace if present (can be set to null)
5. Tag merge (Q5=B):
   a. Apply tags_remove first: task.tags = [t for t in task.tags if t not in tags_remove]
   b. Apply tags add: task.tags = dedupe(task.tags + new_tags)
   (Both steps skipped if neither tags nor tags_remove present in request)
6. Resolve assignee (if present in request)
7. task.updated_at = utcnow()
8. Persist updated task
9. Return TaskResponse
```

---

## Workflow 6: Delete Task (DELETE /tasks/{id})

```
Input: task_id, caller: authenticated user

1. Look up task → 404 if not found or deleted (deleted_at is not None)
2. Check authorization: caller.id == task.owner_id → 403 if not owner
3. Soft delete: task.deleted_at = utcnow(); task.updated_at = utcnow()
4. Persist updated task
5. Return 204 No Content
```

---

## Workflow 7: List Users (GET /users)

```
Input: caller: authenticated user

1. Load all records from users.json (via UserRepository in Unit 1)
2. Map each to UserSummary { id, email, full_name }
   (password_hash and internal fields excluded)
3. Return list[UserSummary]
```

---

## Workflow 8: Get User by ID (GET /users/{id})

```
Input: user_id, caller: authenticated user

1. Look up user by user_id in users.json
2. If not found → 404
3. Return UserSummary { id, email, full_name }
```

---

## Testable Properties (PBT-01 Identification)

### Property 1: Task Serialization Round-Trip (PBT-02 — Round-trip)
```
For all valid Task entities t:
  Task.model_validate(t.model_dump(mode='json')).title == t.title
  (and all other fields preserved)
```
**Category**: Round-trip (serialize → deserialize)
**Generator**: TaskCreate with random valid fields

---

### Property 2: Status Enum Invariant (PBT-03 — Invariant)
```
For all Task entities t:
  t.status in {TaskStatus.todo, TaskStatus.in_progress, TaskStatus.done}
```
**Category**: Invariant

---

### Property 3: Priority Enum Invariant (PBT-03 — Invariant)
```
For all Task entities t:
  t.priority in {TaskPriority.low, TaskPriority.medium, TaskPriority.high}
```
**Category**: Invariant

---

### Property 4: Soft Delete Idempotency (PBT-04 — Idempotence)
```
For any task t:
  state_after_one_delete(t) == state_after_two_deletes(t)
  (deleted_at is not None after 1 or 2 calls to soft_delete(t))
```
**Category**: Idempotence

---

### Property 5: Deleted Tasks Never Appear in List (PBT-03 — Invariant)
```
For any set of tasks S where some are soft-deleted:
  list_tasks(S).filter(t => t.id in deleted_ids) == []
```
**Category**: Invariant

---

### Property 6: Tag Deduplication Invariant (PBT-03 — Invariant)
```
For any tag list with duplicates T:
  len(dedupe(T)) == len(set(T))
  (no duplicate exact-match strings in stored tags)
```
**Category**: Invariant

---

### Property 7: Filter Subset Invariant (PBT-03 — Invariant)
```
For any filter F applied to task set S:
  list_tasks(S, filter=F) ⊆ list_tasks(S)
  (filtered list is always a subset of unfiltered list)
```
**Category**: Invariant

---

## Error Scenarios

| Scenario | Workflow | Rule | HTTP Response |
|---|---|---|---|
| Title missing | Create | BR-TASK-01.1 | 422 |
| Title > 255 chars | Create | BR-TASK-01.1 | 422 |
| Invalid status value | Create/Update | BR-TASK-01.3 | 422 |
| Invalid priority value | Create/Update | BR-TASK-01.4 | 422 |
| Malformed due_date | Create/Update | BR-TASK-01.5 | 422 |
| Tag exceeds 50 chars | Create/Update | BR-TASK-01.7 | 422 |
| assignee_id user not found | Create/Update | BR-TASK-01.9 | 404 |
| assignee_email not registered | Create/Update | BR-TASK-01.10 | 404 |
| Task not found or deleted | Read/Update/Delete | BR-TASK-02.1 | 404 |
| Caller is not owner or assignee | PUT/PATCH | BR-TASK-04.2 | 403 |
| Assignee tries to change assignee | PUT/PATCH | BR-TASK-04.4 | 403 |
| Non-owner tries to delete | Delete | BR-TASK-06.2 | 403 |
| Unauthenticated access | Any | FR-01.6 | 401 |

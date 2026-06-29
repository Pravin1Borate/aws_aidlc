# Functional Design Plan — Unit 2: Task Management

## Plan Execution Checklist

- [x] Ask clarifying questions on ambiguous business logic
- [x] Generate `domain-entities.md`
- [x] Generate `business-rules.md`
- [x] Generate `business-logic-model.md`

---

## Context Already Established (No Questions Needed)

From requirements.md:
- Task fields: title (required), description, status (todo/in_progress/done), priority (low/medium/high), due_date, category (single string), tags (list of strings), owner_id, assignee_id
- Priority default: `medium`; Status default: `todo`
- Owner = creator; only owner can DELETE (FR-06.4)
- Owner AND assignee can read and update (FR-02.4, FR-06.3)
- Category: single free-form string per task (FR-07)
- Tags: multiple free-form strings (FR-08)
- Filtering: status, priority, due_date (FR-09)
- Sort: due_date ascending by default; no-due-date tasks last (FR-09.3)

---

## Questions Requiring User Input

### Q1: Past due date behavior on create/update (FR-05.3)

FR-05.3 says "validation warning, not blocking". What should happen when a due date in the past is submitted?

A) **Allow silently** — accept any date without complaint. Simplest; useful for migrating old tasks.

B) **Return a warning field in the response** — accept the date but include
   `"warnings": ["due_date is in the past"]` in the 201/200 response body. Client can act on it.

C) **Reject with 422** — treat a past due date as a validation error. Strictest; cleanest API.

[Answer]: A

---

### Q2: Task list scope — which tasks does a user see?

FR-02.3 says "list of tasks accessible". What does "accessible" mean for GET /tasks?

A) **Owned OR assigned** — caller sees tasks where `owner_id == caller` OR `assignee_id == caller`.
   Focused view; user only sees their own work.

B) **All tasks in the system** — everyone sees all tasks. Simpler; no filtering by caller.
   Suitable for a shared team board.

[Answer]: B

---

### Q3: Task deletion — hard or soft delete?

A) **Hard delete** — record is permanently removed from `tasks.json`. Simpler; no extra fields needed.

B) **Soft delete** — add `deleted_at: datetime | None` field. Record stays in storage;
   filtered from all list/get responses. Recoverable; slightly more complex.

[Answer]: B

---

### Q4: Assignee lookup — how is the assignee specified?

FR-06.1 says assignable "via user ID or email". What format does the API accept?

A) **User ID (UUID) only** — `"assignee_id": "uuid-string"`. Clients must look up user ID
   first via GET /users. Simple, no ambiguity.

B) **Email only** — `"assignee_email": "user@example.com"`. More user-friendly;
   server resolves to user ID internally.

C) **Both accepted** — accept either `assignee_id` (UUID) or `assignee_email` (string).
   Most flexible; slightly more validation logic.

[Answer]: C

---

### Q5: PATCH tags semantics

On PATCH /tasks/{id}, how should the `tags` field behave?

A) **Replace all** — supplying `"tags": ["x", "y"]` replaces the entire tag list.
   Omitting `tags` from the PATCH body leaves them unchanged.
   Simple, consistent with standard PATCH semantics.

B) **Merge** — supplying `"tags": ["x"]` adds `"x"` to existing tags without removing others.
   Requires a separate mechanism (e.g., `"tags_remove"`) to remove specific tags.
   More granular but more complex.

[Answer]: B


# NFR Requirements Plan — Unit 2: Task Management

## Plan Execution Checklist

- [x] Ask clarifying questions
- [x] Generate `nfr-requirements.md`
- [x] Generate `tech-stack-decisions.md`

---

## Inherited from Unit 1 (No Questions Needed)

Everything already locked:
- bcrypt, python-jose, slowapi, pydantic-settings — locked
- pytest + Hypothesis (pyproject.toml profiles) — locked
- python-json-logger, CorrelationIdMiddleware — locked
- Rate limits: 100 req/min per authenticated user — locked
- Health checks: already implemented — no new endpoints needed

---

## Questions Requiring User Input

### Q1: Task list pagination

The requirements note pagination is "optional for MVP". Add it now or skip?

A) **Skip** — no pagination; `GET /tasks` returns all matching tasks. Acceptable for
   local dev with a small number of tasks.

B) **Add basic pagination** — optional `?limit=50&offset=0` query params.
   Defaults: limit=100, offset=0. Returns `{"items": [...], "total": N}`.
   Minor extra code but better API design for future use.

[Answer]: B

---

### Q2: Cross-service user data access

`TaskService` needs to look up users for assignee resolution and `GET /users`.
How should Unit 2 access `users.json`?

A) **Reuse `UserRepository` directly** — import `UserRepository` from `src.auth.repository`
   and instantiate it with the same `users.json` path. Shares the storage layer cleanly;
   already designed as a stable interface in unit-of-work-dependency.md.

B) **New `UserReadRepository`** — a separate lightweight read-only repository in
   `src/users/repository.py` that reads `users.json` but cannot write to it.
   Cleaner separation but duplicates some code.

[Answer]: B

---

### Q3: Task repository — additional query method for due-date filtering

For `GET /tasks?due_date=YYYY-MM-DD`, the filter finds tasks due on or before the given date.
Where should this filter logic live?

A) **In `TaskService`** — `TaskRepository.find_all()` returns all non-deleted tasks;
   filtering and sorting happens in the service layer. Simple; storage stays generic.

B) **In `TaskRepository`** — `find_filtered(status, priority, due_date)` handles
   the SQL-equivalent WHERE clause. Keeps service thinner; slightly couples repository
   to domain query logic.

[Answer]: B


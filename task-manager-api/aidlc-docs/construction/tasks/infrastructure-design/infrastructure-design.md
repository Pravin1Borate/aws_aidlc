# Infrastructure Design — Unit 2: Task Management

## Inherited from Unit 1 (all unchanged)

| Concern | Decision |
|---|---|
| Deployment target | Local development only |
| Compute | Single uvicorn process, `--reload` |
| Run method | `uvicorn src.main:app --host $APP_HOST --port $APP_PORT --reload` |
| CORS | Permissive `allow_origins=["*"]` (local dev) |
| Logging | stdout JSON lines (python-json-logger) |
| Config | pydantic-settings + `.env` file |
| Health checks | `/health/live` + `/health/ready` (Unit 1) |

---

## Unit 2 Additions

### Storage

| File | Created By | Location |
|---|---|---|
| `users.json` | Unit 1 — on first registration | `$DATA_DIR/users.json` |
| `tasks.json` | Unit 2 — on first task creation | `$DATA_DIR/tasks.json` |

Both files share the same `DATA_DIR`. The `data/` directory is created at startup by the Unit 1 lifespan event — no additional startup logic needed for Unit 2.

### New API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/tasks` | List all tasks (paginated, filterable) |
| POST | `/tasks` | Create a task |
| GET | `/tasks/{task_id}` | Get task by ID |
| PUT | `/tasks/{task_id}` | Full update |
| PATCH | `/tasks/{task_id}` | Partial update |
| DELETE | `/tasks/{task_id}` | Soft delete |
| GET | `/users` | List all registered users |
| GET | `/users/{user_id}` | Get user by ID |

### No New Environment Variables

All configuration already covered:
```dotenv
JWT_SECRET_KEY=...       # Unit 1
JWT_EXPIRY_MINUTES=60    # Unit 1
DATA_DIR=./data          # covers both users.json and tasks.json
APP_HOST=127.0.0.1       # Unit 1
APP_PORT=8000            # Unit 1
LOG_LEVEL=INFO           # Unit 1
```

---

## Security Boundaries (unchanged)

All security boundaries from Unit 1 apply. Unit 2 adds object-level authorization (owner/assignee check on every task mutation) — this is application-level, not infrastructure-level.

---

## Extension Compliance

| Rule | Status | Notes |
|---|---|---|
| SECURITY-11 (Rate limiting) | Compliant | All 8 new endpoints decorated with `@limiter.limit("100/minute")` |
| SECURITY-08 (Access control) | Compliant | `get_current_user` dependency on all new endpoints |
| RESILIENCY-04 (Health checks) | Compliant | Inherited from Unit 1 — no new checks needed |
| Others | N/A | Local dev scope |

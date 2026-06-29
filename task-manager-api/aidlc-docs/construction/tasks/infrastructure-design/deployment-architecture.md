# Deployment Architecture — Unit 2: Task Management

## Updated Runtime Directory Structure

```
task-manager-api/
├── src/
│   ├── auth/                    ← Unit 1 (unchanged)
│   ├── core/
│   │   ├── errors.py            ← Unit 1 (unchanged)
│   │   ├── health.py            ← Unit 1 (unchanged)
│   │   ├── logging.py           ← Unit 1 (unchanged)
│   │   ├── middleware.py        ← Unit 1 (unchanged)
│   │   ├── rate_limiter.py      ← Unit 1 (unchanged)
│   │   ├── schemas.py           ← Unit 2 NEW (PaginatedResponse[T])
│   │   └── storage.py           ← Unit 1 (unchanged)
│   ├── tasks/                   ← Unit 2 NEW
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── schemas.py
│   ├── users/                   ← Unit 2 NEW
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   └── repository.py
│   ├── config.py                ← Unit 1 (unchanged)
│   ├── dependencies.py          ← Unit 1 + Unit 2 additions
│   └── main.py                  ← Unit 1 + 2 new include_router() calls
├── tests/
│   ├── conftest.py              ← Unit 1 (unchanged)
│   ├── unit/
│   │   ├── auth/                ← Unit 1
│   │   ├── tasks/               ← Unit 2 NEW
│   │   └── users/               ← Unit 2 NEW
│   ├── integration/
│   │   ├── auth/                ← Unit 1
│   │   └── tasks/               ← Unit 2 NEW
│   └── pbt/
│       ├── auth/                ← Unit 1
│       └── tasks/               ← Unit 2 NEW
├── data/                        ← runtime (gitignored)
│   ├── users.json               ← Unit 1 (created on first registration)
│   └── tasks.json               ← Unit 2 (created on first task creation)
├── .env                         ← unchanged
├── .env.example                 ← unchanged
├── .gitignore                   ← unchanged
├── pyproject.toml               ← unchanged
├── requirements.txt             ← unchanged (no new deps)
└── requirements-dev.txt         ← unchanged
```

---

## Process Architecture (Updated)

```
Developer Machine
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   uvicorn process (single worker)                       │
│   ┌─────────────────────────────────────────────────┐  │
│   │  FastAPI app                                    │  │
│   │  ├── CORSMiddleware                             │  │
│   │  ├── CorrelationIdMiddleware                    │  │
│   │  ├── SlowAPIMiddleware                          │  │
│   │  ├── auth_router   (/auth/*)     Unit 1         │  │
│   │  ├── health_router (/health/*)   Unit 1         │  │
│   │  ├── task_router   (/tasks/*)    Unit 2 NEW     │  │
│   │  └── user_router   (/users/*)    Unit 2 NEW     │  │
│   │                                                 │  │
│   │  In-memory:                                     │  │
│   │  └── token_blacklist: set[str]   Unit 1         │  │
│   └─────────────────────────────────────────────────┘  │
│         ↕ JSON reads/writes                             │
│   ┌──────────────────────────────────┐                 │
│   │  ./data/users.json   (Unit 1)    │                 │
│   │  ./data/tasks.json   (Unit 2)    │                 │
│   └──────────────────────────────────┘                 │
│                                                         │
│   Logs → stdout (terminal)                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Full API Surface (after Unit 2)

```
Public (no auth):
  POST /auth/register
  POST /auth/login
  GET  /health/live
  GET  /health/ready

Authenticated:
  POST   /auth/logout
  GET    /auth/me

  GET    /tasks                    paginated, filterable
  POST   /tasks
  GET    /tasks/{task_id}
  PUT    /tasks/{task_id}
  PATCH  /tasks/{task_id}
  DELETE /tasks/{task_id}

  GET    /users
  GET    /users/{user_id}
```

---

## Startup Sequence (unchanged from Unit 1)

No changes to startup. `DATA_DIR` creation in the lifespan event already covers `tasks.json` since it shares the same directory.

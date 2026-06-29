# Application Design — Consolidated Overview

## Architecture Summary

**Style**: By-feature packages with shared `core/` infrastructure
**Tier pattern**: Router → Service → Repository (three-tier)
**Framework**: FastAPI (Python 3.11+)
**Storage**: JSON file persistence via `JsonFileStorage`
**Auth**: JWT (stateless tokens + in-memory blacklist)

---

## Project Structure

```
task-manager-api/
├── main.py              # App factory, middleware and router registration
├── config.py            # pydantic-settings: all env var config
├── dependencies.py      # FastAPI DI factories (get_current_user, service factories)
│
├── auth/                # Unit 1: Authentication
│   ├── router.py        # POST /auth/register, /auth/login, /auth/logout
│   ├── service.py       # AuthService: register, login, logout, get_current_user
│   ├── repository.py    # UserRepository: CRUD on users.json
│   └── models.py        # UserCreate, LoginRequest, TokenResponse, UserResponse
│
├── tasks/               # Unit 2: Task Management
│   ├── router.py        # GET/POST /tasks, GET/PUT/PATCH/DELETE /tasks/{id}
│   ├── service.py       # TaskService: create/get/list/update/delete + filters
│   ├── repository.py    # TaskRepository: CRUD on tasks.json
│   └── models.py        # TaskCreate, TaskUpdate, TaskPatch, TaskResponse, enums
│
├── users/               # User discovery (read-only, part of Unit 2)
│   ├── router.py        # GET /users, GET /users/{id}, GET /health
│   ├── service.py       # UserService: list_users, get_user
│   └── models.py        # UserPublicResponse
│
├── core/                # Shared infrastructure (no business logic)
│   ├── storage.py       # JsonFileStorage: atomic file read/write
│   ├── security.py      # JWT encode/decode, bcrypt hash/verify, token blacklist
│   ├── rate_limiter.py  # RateLimiterMiddleware: per-user/IP limits, 429 responses
│   ├── logging.py       # Structured JSON logger (SECURITY-03 compliant)
│   └── errors.py        # AppException hierarchy + global FastAPI error handlers
│
├── data/                # Runtime data directory (gitignored)
│   ├── users.json       # User records
│   └── tasks.json       # Task records
│
├── tests/
│   ├── unit/            # Unit tests per service/repository
│   ├── integration/     # API-level integration tests (TestClient)
│   └── pbt/             # Hypothesis property-based tests
│
├── .env                 # Local environment variables (gitignored)
├── .env.example         # Example env file (committed)
├── requirements.txt     # Pinned dependencies
└── requirements-dev.txt # Dev/test dependencies (pytest, hypothesis, httpx)
```

---

## Component Summary

| Component | Package | Role | Tier |
|---|---|---|---|
| AuthRouter | `auth/router.py` | HTTP handlers for auth endpoints | Router |
| AuthService | `auth/service.py` | Auth business logic + JWT lifecycle | Service |
| UserRepository | `auth/repository.py` | User data persistence (users.json) | Repository |
| TaskRouter | `tasks/router.py` | HTTP handlers for task endpoints | Router |
| TaskService | `tasks/service.py` | Task business logic + authorization | Service |
| TaskRepository | `tasks/repository.py` | Task data persistence (tasks.json) | Repository |
| UserRouter | `users/router.py` | HTTP handlers for user discovery | Router |
| UserService | `users/service.py` | Read-only user listing | Service |
| JsonFileStorage | `core/storage.py` | Atomic JSON file I/O | Infrastructure |
| SecurityUtils | `core/security.py` | JWT + bcrypt + token blacklist | Infrastructure |
| RateLimiterMiddleware | `core/rate_limiter.py` | Rate limiting (SECURITY-11) | Middleware |
| StructuredLogger | `core/logging.py` | JSON logging (SECURITY-03) | Infrastructure |
| ErrorHandlers | `core/errors.py` | Global exception handling (SECURITY-15) | Infrastructure |
| Settings | `config.py` | Environment configuration | Config |

---

## Key Design Principles

### 1. Separation of Concerns
- **Routers**: HTTP only — parse input, call service, serialize output
- **Services**: Business logic only — enforce rules, orchestrate, raise typed exceptions
- **Repositories**: Data I/O only — no business logic or HTTP concerns
- **Core**: Infrastructure only — no feature-specific logic

### 2. No Cross-Feature Service Calls
Features communicate through shared repositories only. `TaskService` reads user data via `UserRepository` directly — it does not call `UserService`. This prevents circular dependencies and keeps the service layer clean.

### 3. Security by Design
- All routes require JWT auth by default via `get_current_user` dependency
- Public routes (`/auth/register`, `/auth/login`, `/health`) explicitly opt out
- Rate limiting applied at middleware level before any business logic
- Global error handlers ensure no stack traces reach API consumers

### 4. Testability
- All services receive their dependencies via constructor injection — easily mockable
- `JsonFileStorage` backed by a configurable file path — tests can use temp files
- No global state except the token blacklist (in-memory set, reset between tests)

---

## API Endpoint Map

| Method | Path | Router | Auth | Rate Limit |
|---|---|---|---|---|
| POST | `/auth/register` | AuthRouter | Public | Unauth limit |
| POST | `/auth/login` | AuthRouter | Public | Unauth limit |
| POST | `/auth/logout` | AuthRouter | Required | Auth limit |
| GET | `/tasks` | TaskRouter | Required | Auth limit |
| POST | `/tasks` | TaskRouter | Required | Auth limit |
| GET | `/tasks/{id}` | TaskRouter | Required | Auth limit |
| PUT | `/tasks/{id}` | TaskRouter | Required | Auth limit |
| PATCH | `/tasks/{id}` | TaskRouter | Required | Auth limit |
| DELETE | `/tasks/{id}` | TaskRouter | Required | Auth limit |
| GET | `/users` | UserRouter | Required | Auth limit |
| GET | `/users/{id}` | UserRouter | Required | Auth limit |
| GET | `/health` | UserRouter | Public | Unauth limit |

---

## Extension Compliance Notes

### Security Baseline
- SECURITY-03: StructuredLogger in `core/logging.py` — JSON format, no PII
- SECURITY-08: `get_current_user` dependency on all protected routes; object-level auth in TaskService
- SECURITY-09: ErrorHandlers return generic messages; no stack traces
- SECURITY-11: RateLimiterMiddleware on all endpoints
- SECURITY-12: SecurityUtils uses bcrypt; no plain-text passwords
- SECURITY-15: Global error handlers + try/finally patterns in repositories

### Resiliency Baseline
- RESILIENCY-05: StructuredLogger + `/health` endpoint (RESILIENCY-06)
- RESILIENCY-10: JsonFileStorage uses explicit timeout/error handling on file I/O

### Property-Based Testing
- PBT-09: Hypothesis framework (Python) — selected and documented
- PBT test files located in `tests/pbt/`
- Properties to identify during Functional Design (PBT-01)

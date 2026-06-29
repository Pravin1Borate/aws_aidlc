# Components

## Architecture Overview

**Pattern**: By-feature packages with shared `core/` package
**Tier structure**: Router → Service → Repository (three-tier per unit)

```
task-manager-api/
├── main.py              # App entry point, router registration, middleware wiring
├── config.py            # Settings (pydantic-settings, env vars)
├── dependencies.py      # FastAPI dependency injection (current_user, rate_limit)
├── auth/                # Feature: Authentication
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   └── models.py
├── tasks/               # Feature: Task Management
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   └── models.py
├── users/               # Feature: User Discovery (read-only)
│   ├── router.py
│   ├── service.py
│   └── models.py
└── core/                # Shared infrastructure
    ├── storage.py       # Generic JSON file CRUD
    ├── security.py      # JWT + password hashing
    ├── rate_limiter.py  # Rate limiting middleware
    ├── logging.py       # Structured JSON logger
    └── errors.py        # Exception classes + global handlers
```

---

## Feature Components

### AuthRouter (`auth/router.py`)

**Responsibility**: Handle HTTP requests for authentication endpoints. Validate request shapes, delegate to AuthService, return HTTP responses.

**Endpoints owned**:
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`

**Interface**: FastAPI `APIRouter`, mounted at `/auth`

---

### AuthService (`auth/service.py`)

**Responsibility**: Orchestrate authentication business logic. Coordinate between UserRepository, SecurityUtils, and token blacklist. Enforce auth business rules (duplicate email, credential verification, token lifecycle).

**Interface**: Plain Python class, injected into AuthRouter via FastAPI dependency

---

### UserRepository (`auth/repository.py`)

**Responsibility**: All persistence operations for User entities. Read from and write to `users.json`. Owns the User data schema on disk.

**Interface**: Plain Python class backed by `core/storage.py`; injected into AuthService

---

### TaskRouter (`tasks/router.py`)

**Responsibility**: Handle HTTP requests for task CRUD and management endpoints. Apply JWT auth dependency. Validate request shapes, delegate to TaskService, return HTTP responses.

**Endpoints owned**:
- `GET /tasks`
- `POST /tasks`
- `GET /tasks/{task_id}`
- `PUT /tasks/{task_id}`
- `PATCH /tasks/{task_id}`
- `DELETE /tasks/{task_id}`

**Interface**: FastAPI `APIRouter`, mounted at `/tasks`

---

### TaskService (`tasks/service.py`)

**Responsibility**: Orchestrate task business logic. Enforce ownership and authorization rules (who can read, update, delete). Apply filtering logic. Coordinate with UserRepository to validate assignees.

**Interface**: Plain Python class, injected into TaskRouter via FastAPI dependency

---

### TaskRepository (`tasks/repository.py`)

**Responsibility**: All persistence operations for Task entities. Read from and write to `tasks.json`. Owns the Task data schema on disk.

**Interface**: Plain Python class backed by `core/storage.py`; injected into TaskService

---

### UserRouter (`users/router.py`)

**Responsibility**: Handle HTTP requests for user discovery endpoints. Requires JWT auth.

**Endpoints owned**:
- `GET /users`
- `GET /users/{user_id}`
- `GET /health`

**Interface**: FastAPI `APIRouter`, mounted at `/users`

---

### UserService (`users/service.py`)

**Responsibility**: Orchestrate user listing logic. Serves read-only user data (no passwords) for assignee selection.

**Interface**: Plain Python class, injected into UserRouter via FastAPI dependency

---

## Core Infrastructure Components

### JsonFileStorage (`core/storage.py`)

**Responsibility**: Generic JSON file read/write operations. Single source of truth for file I/O. Handles atomic writes (write-to-temp → rename) to prevent data corruption on partial writes.

**Interface**: Generic utility class used by UserRepository and TaskRepository

---

### SecurityUtils (`core/security.py`)

**Responsibility**: JWT token creation, decoding, and validation. Password hashing (bcrypt/argon2) and verification. Token blacklist management (in-memory set for local dev).

**Interface**: Module-level functions used by AuthService and the `get_current_user` dependency

---

### RateLimiter (`core/rate_limiter.py`)

**Responsibility**: FastAPI middleware that enforces per-user/IP request rate limits. Returns HTTP 429 with `Retry-After` header when limit is exceeded. Satisfies SECURITY-11 and FR-10.

**Interface**: FastAPI `BaseHTTPMiddleware`, registered on the app in `main.py`

---

### StructuredLogger (`core/logging.py`)

**Responsibility**: Configure application-wide structured JSON logging. Ensures every log entry includes timestamp, request ID, log level, and message. Ensures no PII or tokens are logged. Satisfies SECURITY-03.

**Interface**: Module-level `get_logger()` function returning a configured logger instance

---

### ErrorHandlers (`core/errors.py`)

**Responsibility**: Define custom application exception classes (`AppException`, `NotFoundError`, `ForbiddenError`, `ConflictError`, `UnauthorizedError`). Register global FastAPI exception handlers that return generic, sanitised HTTP responses. Satisfies SECURITY-09 and SECURITY-15.

**Interface**: Exception classes + `register_error_handlers(app)` function called in `main.py`

---

### Settings (`config.py`)

**Responsibility**: Load and validate all environment configuration at startup using pydantic-settings. Single source of truth for env vars.

**Key settings**:
- `JWT_SECRET_KEY` — signing secret (required, no default)
- `JWT_ALGORITHM` — default `HS256`
- `JWT_EXPIRY_MINUTES` — default `60`
- `DATA_DIR` — path to JSON data files (default `./data`)
- `LOG_LEVEL` — default `INFO`
- `RATE_LIMIT_AUTHENTICATED` — default `100` req/min
- `RATE_LIMIT_UNAUTHENTICATED` — default `20` req/min

**Interface**: Singleton `settings` instance imported by all components that need config

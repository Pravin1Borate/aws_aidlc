# Units of Work

## Overview

**Deployment model**: Monolith — single FastAPI application, logically separated by feature package
**Unit count**: 2
**Development sequence**: Sequential (Unit 1 → Unit 2)

---

## Unit 1: Authentication

### Identity
- **Name**: Authentication
- **Short name**: `auth`
- **Type**: Feature unit within a monolith
- **Business criticality**: Critical (all other units depend on it)

### Scope
**Package ownership**:
- `auth/` — router, service, repository, Pydantic models
- `core/security.py` — JWT encode/decode, bcrypt hashing, token blacklist
- `core/errors.py` — AppException hierarchy, global FastAPI error handlers
- `core/logging.py` — Structured JSON logger configuration
- `config.py` — Settings (pydantic-settings, all environment variables)
- `dependencies.py` — `get_current_user` FastAPI dependency + service factories
- `main.py` — FastAPI app factory, router registration, middleware wiring (bootstrap)
- `data/users.json` — User persistence file (created on first write)

**Stories in scope**: US-01, US-02, US-03, US-04

### Responsibilities
1. Register new user accounts (email + password, bcrypt-hashed)
2. Authenticate users and issue signed JWT access tokens
3. Invalidate tokens on logout (in-memory blacklist)
4. Validate tokens on every protected request via `get_current_user` dependency
5. Enforce brute-force protection patterns (per SECURITY-12)
6. Provide structured JSON logging infrastructure for the entire app
7. Provide global error handling (no stack traces in responses)
8. Provide app-wide environment configuration

### Deliverables
- `POST /auth/register` — creates user, returns user profile (no password)
- `POST /auth/login` — verifies credentials, returns JWT token
- `POST /auth/logout` — blacklists token
- `get_current_user` FastAPI dependency (reusable by Unit 2)
- `UserRepository` (reusable by Unit 2 for assignee validation)
- Structured logging infrastructure (reusable by Unit 2)
- Global error handlers (shared)
- Full test suite: example-based (pytest) + PBT (Hypothesis)

### Code Organisation
```
task-manager-api/
├── main.py
├── config.py
├── dependencies.py
├── auth/
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   └── models.py
├── core/
│   ├── __init__.py
│   ├── security.py
│   ├── errors.py
│   └── logging.py
├── data/
│   └── users.json
└── tests/
    ├── unit/auth/
    ├── integration/auth/
    └── pbt/auth/
```

---

## Unit 2: Task Management

### Identity
- **Name**: Task Management
- **Short name**: `tasks`
- **Type**: Feature unit within a monolith
- **Business criticality**: High (core product functionality)

### Scope
**Package ownership**:
- `tasks/` — router, service, repository, Pydantic models
- `users/` — router, service, Pydantic models (user discovery, read-only)
- `core/storage.py` — JsonFileStorage (generic atomic JSON I/O)
- `core/rate_limiter.py` — RateLimiterMiddleware (registered in main.py)
- `data/tasks.json` — Task persistence file (created on first write)

**Stories in scope**: US-05 through US-22

### Responsibilities
1. Full task CRUD (create, read, update, delete) with UUID-based identity
2. Task organisation: priority (low/medium/high), status (todo/in_progress/done), due date, category, tags
3. Task assignment to any registered user; ownership-based access control
4. Task filtering: by status, priority, due date (AND composition)
5. User discovery: list all users and get user by ID (for assignee selection)
6. Rate limiting on all endpoints (authenticated: 100/min, unauthenticated: 20/min)
7. Health check endpoint

### Deliverables
- `GET /tasks` — list accessible tasks with optional filters
- `POST /tasks` — create task
- `GET /tasks/{id}` — get task by ID
- `PUT /tasks/{id}` — full replace (owner only)
- `PATCH /tasks/{id}` — partial update (owner or assignee)
- `DELETE /tasks/{id}` — delete (owner only)
- `GET /users` — list all users (public fields only)
- `GET /users/{id}` — get user by ID
- `GET /health` — health check (public)
- Rate limiting middleware (applied to all endpoints)
- Full test suite: example-based (pytest) + PBT (Hypothesis)

### Code Organisation
```
task-manager-api/
├── tasks/
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   └── models.py
├── users/
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   └── models.py
├── core/
│   ├── storage.py
│   └── rate_limiter.py
├── data/
│   └── tasks.json
└── tests/
    ├── unit/tasks/
    ├── unit/users/
    ├── integration/tasks/
    ├── integration/users/
    └── pbt/tasks/
```

---

## Combined Project Structure (Both Units Complete)

```
task-manager-api/
├── main.py
├── config.py
├── dependencies.py
├── auth/
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   └── models.py
├── tasks/
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   └── models.py
├── users/
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   └── models.py
├── core/
│   ├── __init__.py
│   ├── security.py
│   ├── storage.py
│   ├── rate_limiter.py
│   ├── logging.py
│   └── errors.py
├── data/
│   ├── users.json
│   └── tasks.json
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── auth/
│   │   ├── tasks/
│   │   └── users/
│   ├── integration/
│   │   ├── auth/
│   │   ├── tasks/
│   │   └── users/
│   └── pbt/
│       ├── auth/
│       └── tasks/
├── .env
├── .env.example
├── requirements.txt
└── requirements-dev.txt
```

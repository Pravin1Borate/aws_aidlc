# Task Manager API

A RESTful API for task management with user authentication, built with Python and FastAPI. Features JWT-based auth, task CRUD with priority levels, due date tracking, tag management, user assignment, and paginated filtering.

> **Scope**: Local development / proof-of-concept. See [Known Limitations](#known-limitations) before deploying to production.

---

## Features

- **User authentication** — register, login, logout with JWT tokens
- **Account security** — bcrypt password hashing (cost-12), account lockout after 5 failed logins (15 min)
- **Task management** — create, read, update, delete with soft-delete semantics
- **Priority levels** — `low`, `medium` (default), `high`
- **Status tracking** — `todo` (default), `in_progress`, `done`
- **Due dates** — optional ISO 8601 date (`YYYY-MM-DD`)
- **Categories & tags** — free-form category, tag list with merge/remove semantics on PATCH
- **User assignment** — assign by user ID or email; owner and assignee can edit, only owner can delete/reassign
- **Filtering** — filter tasks by status, priority, and due date (on or before)
- **Pagination** — all list endpoints return `PaginatedResponse` with `total`, `limit`, `offset`
- **Rate limiting** — 20/min on public endpoints, 100/min on authenticated endpoints
- **Structured logging** — JSON lines to stdout with correlation ID on every request
- **Health checks** — liveness and readiness probes

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.111.1 |
| Server | uvicorn 0.30.1 |
| Validation | Pydantic v2 |
| Auth | python-jose (JWT HS256) + bcrypt |
| Storage | JSON flat files (`data/users.json`, `data/tasks.json`) |
| Rate limiting | slowapi |
| Logging | python-json-logger |
| Config | pydantic-settings + `.env` |
| Testing | pytest + httpx + Hypothesis (PBT) |

---

## Prerequisites

- Python **3.11 or higher**
- pip (included with Python)

Verify:
```bash
python --version   # must be 3.11+
```

---

## Quick Start

### 1. Enter the project directory

```bash
cd task-manager-api
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set the required `JWT_SECRET_KEY`:

```dotenv
# Generate a secure key:  python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=your-secret-key-here

JWT_EXPIRY_MINUTES=60
DATA_DIR=./data
APP_HOST=127.0.0.1
APP_PORT=8000
LOG_LEVEL=INFO
```

### 5. Start the server

```bash
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

The API is now running at **http://127.0.0.1:8000**

- Interactive docs (Swagger UI): http://127.0.0.1:8000/docs
- Alternative docs (ReDoc): http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health/live

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `JWT_SECRET_KEY` | **Yes** | — | Secret key for signing JWTs. Must be set — app refuses to start without it. |
| `JWT_EXPIRY_MINUTES` | No | `60` | Token lifetime in minutes |
| `DATA_DIR` | No | `./data` | Directory for JSON data files |
| `APP_HOST` | No | `127.0.0.1` | Bind address for uvicorn |
| `APP_PORT` | No | `8000` | Port for uvicorn |
| `LOG_LEVEL` | No | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

> `.env` is gitignored. Never commit it.

---

## API Reference

### Authentication

All task and user endpoints require a Bearer token obtained from `POST /auth/login`.

Include it in every authenticated request:
```
Authorization: Bearer <your_access_token>
```

---

### Auth Endpoints

#### Register

```http
POST /auth/register
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "MyPassword1",
  "full_name": "Alice Smith"
}
```

Response `201 Created`:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "alice@example.com",
  "full_name": "Alice Smith",
  "created_at": "2025-01-01T10:00:00Z"
}
```

Errors: `409` email already registered, `422` invalid email or password too short (min 8 chars).

---

#### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "MyPassword1"
}
```

Response `200 OK`:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

Errors: `401` wrong credentials, `423` account locked (5 failed attempts → 15 min lockout).

---

#### Logout

```http
POST /auth/logout
Authorization: Bearer <token>
```

Response `200 OK`. The token is blacklisted immediately (cannot be reused).

---

#### Get Current User

```http
GET /auth/me
Authorization: Bearer <token>
```

Response `200 OK`:
```json
{
  "id": "550e8400-...",
  "email": "alice@example.com",
  "full_name": "Alice Smith",
  "created_at": "2025-01-01T10:00:00Z"
}
```

---

### Task Endpoints

All task endpoints require authentication.

#### List Tasks (with filtering and pagination)

```http
GET /tasks/?status=todo&priority=high&due_date=2025-12-31&limit=20&offset=0
Authorization: Bearer <token>
```

Query parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `status` | `todo` \| `in_progress` \| `done` | — | Filter by status |
| `priority` | `low` \| `medium` \| `high` | — | Filter by priority |
| `due_date` | `YYYY-MM-DD` | — | Return tasks with due_date ≤ this date |
| `limit` | integer (1–500) | `100` | Page size |
| `offset` | integer (≥0) | `0` | Number of records to skip |

Response `200 OK`:
```json
{
  "items": [
    {
      "id": "abc123",
      "title": "Buy groceries",
      "description": null,
      "status": "todo",
      "priority": "high",
      "due_date": "2025-12-31",
      "category": "personal",
      "tags": ["shopping", "urgent"],
      "owner_id": "user-uuid",
      "assignee_id": null,
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-01T10:00:00Z"
    }
  ],
  "total": 47,
  "limit": 20,
  "offset": 0
}
```

Results are sorted by `due_date` ascending; tasks with no due date appear last. Multiple filters are ANDed together.

---

#### Create Task

```http
POST /tasks/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "status": "todo",
  "priority": "high",
  "due_date": "2025-12-31",
  "category": "personal",
  "tags": ["shopping", "urgent"],
  "assignee_id": "user-uuid",
  "assignee_email": "bob@example.com"
}
```

Only `title` is required. All other fields are optional.

`assignee_id` takes precedence over `assignee_email` if both are provided. The referenced user must exist.

Response `201 Created`: full `TaskResponse` object (same shape as list items).

Errors: `422` validation error, `404` assignee not found.

---

#### Get Task by ID

```http
GET /tasks/{task_id}
Authorization: Bearer <token>
```

Any authenticated user can read any active task.

Response `200 OK`: `TaskResponse` object.  
Errors: `404` task not found or deleted.

---

#### Full Update (PUT)

Replaces **all mutable fields**. Omitted optional fields revert to `None`/default.

```http
PUT /tasks/{task_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Updated title",
  "status": "in_progress",
  "priority": "medium"
}
```

Only the task owner or assignee may call this. Only the owner may change the assignee.

Response `200 OK`: updated `TaskResponse`.  
Errors: `403` not owner/assignee, `404` not found.

---

#### Partial Update (PATCH)

Updates **only provided fields**. Unset fields are unchanged.

```http
PATCH /tasks/{task_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "done",
  "tags": ["new-tag"],
  "tags_remove": ["old-tag"]
}
```

**Tag merge semantics**: `tags_remove` is applied first (removes by exact match), then `tags` are added, with deduplication. Existing tags not mentioned are preserved.

Response `200 OK`: updated `TaskResponse`.

---

#### Delete Task (Soft Delete)

```http
DELETE /tasks/{task_id}
Authorization: Bearer <token>
```

Only the task **owner** can delete. The record is soft-deleted (kept in storage, invisible to all read/list/update operations).

Response `204 No Content`.  
Errors: `403` not owner, `404` not found.

---

### User Endpoints

#### List All Users

```http
GET /users/
Authorization: Bearer <token>
```

Response `200 OK`:
```json
[
  { "id": "user-uuid", "email": "alice@example.com", "full_name": "Alice Smith" },
  { "id": "user-uuid-2", "email": "bob@example.com", "full_name": "Bob Jones" }
]
```

Password hashes and internal fields are never returned.

---

#### Get User by ID

```http
GET /users/{user_id}
Authorization: Bearer <token>
```

Response `200 OK`: single `UserSummary` object.  
Errors: `404` user not found.

---

### Health Endpoints

```http
GET /health/live    # Always 200 OK — process is alive
GET /health/ready   # 200 OK if JWT configured + data dir writable; 503 otherwise
```

---

## Project Structure

```
task-manager-api/
├── src/
│   ├── auth/                   # Authentication feature
│   │   ├── repository.py       # UserRepository — read/write users.json
│   │   ├── router.py           # /auth/* endpoints
│   │   ├── schemas.py          # User models (UserCreate, LoginRequest, TokenResponse...)
│   │   └── service.py          # AuthService — register, login, logout, get_current_user
│   ├── core/                   # Shared infrastructure
│   │   ├── errors.py           # AppException hierarchy (401, 403, 404, 409)
│   │   ├── health.py           # /health/live + /health/ready
│   │   ├── logging.py          # JSON logging setup
│   │   ├── middleware.py       # CorrelationIdMiddleware
│   │   ├── rate_limiter.py     # slowapi limiter singleton
│   │   ├── schemas.py          # PaginatedResponse[T] generic
│   │   ├── security.py         # bcrypt, JWT, token blacklist
│   │   └── storage.py          # JsonFileStorage — atomic read/write
│   ├── tasks/                  # Task management feature
│   │   ├── repository.py       # TaskRepository — find_by_id, find_filtered, save
│   │   ├── router.py           # /tasks/* endpoints
│   │   ├── schemas.py          # Task, TaskCreate, TaskUpdate, TaskPatch, TaskResponse...
│   │   └── service.py          # TaskService — CRUD + access control + tag merge
│   ├── users/                  # User read feature
│   │   ├── repository.py       # UserReadRepository — read-only view of users.json
│   │   ├── router.py           # /users/* endpoints
│   │   ├── schemas.py          # UserSummary
│   │   └── service.py          # UserService — list, get_by_id
│   ├── config.py               # Settings (pydantic-settings + .env)
│   ├── dependencies.py         # FastAPI dependency factories
│   └── main.py                 # App factory, middleware, routers, lifespan
├── tests/
│   ├── conftest.py             # Shared fixtures (client, tmp_data_dir, patch_settings)
│   ├── unit/
│   │   ├── auth/               # Auth unit tests (security utils, service, repository)
│   │   ├── tasks/              # Task unit tests (repository, service)
│   │   └── users/              # User unit tests (service)
│   ├── integration/
│   │   ├── auth/               # Auth endpoint integration tests
│   │   └── tasks/              # Task + user endpoint integration tests
│   └── pbt/
│       ├── auth/               # Hypothesis properties — JWT, password, blacklist
│       └── tasks/              # Hypothesis properties — tag merge, response invariants
├── data/                       # Runtime data (gitignored)
│   ├── users.json
│   └── tasks.json
├── aidlc-docs/                 # AI-DLC documentation (design, requirements, audit)
├── .env.example                # Environment variable template
├── .gitignore
├── pyproject.toml              # pytest + coverage + Hypothesis configuration
├── requirements.txt            # Runtime dependencies
└── requirements-dev.txt        # Dev/test dependencies
```

---

## Running Tests

Install dev dependencies first:

```bash
pip install -r requirements-dev.txt
```

### All tests with coverage

```bash
python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=80
```

### By category

```bash
# Unit tests only (fast, no I/O)
python -m pytest tests/unit/ -v

# Integration tests (full HTTP stack, isolated temp DB per test)
python -m pytest tests/integration/ -v

# Property-based tests (Hypothesis)
python -m pytest tests/pbt/ -v
```

### Single test

```bash
python -m pytest tests/unit/tasks/test_task_service.py::TestCreate::test_creates_task_with_defaults -v -s
```

### Coverage HTML report

```bash
python -m pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html
```

**Test inventory (~130 tests):**

| Category | Count |
|---|---|
| Unit — auth | 37 |
| Unit — tasks | 32 |
| Unit — users | 5 |
| Integration — auth | 16 |
| Integration — tasks + users | 27 |
| Property-based (Hypothesis) | 13 |

---

## Access Control Rules

| Operation | Who can perform it |
|---|---|
| Read any task | Any authenticated user |
| Create task | Any authenticated user (becomes owner) |
| Edit task (PUT/PATCH) | Owner **or** assignee |
| Change assignee | Owner only |
| Delete task | Owner only |
| Read any user | Any authenticated user |

---

## Tag Merge Semantics (PATCH)

PATCH uses merge semantics, not replacement:

```json
{ "tags": ["new"], "tags_remove": ["old"] }
```

1. `tags_remove` is applied first — removes matching tags from the existing list
2. `tags` are then added to the result
3. Duplicates are removed (case-sensitive)

Example: existing `["a", "b", "c"]` + PATCH `{"tags": ["d"], "tags_remove": ["b"]}` → `["a", "c", "d"]`

---

## Known Limitations

This project is scoped for **local development**. The following must be addressed before any production use:

| Limitation | Detail |
|---|---|
| JSON file storage | Not safe for concurrent writes; no transactions; data lost if process crashes mid-write. Replace with PostgreSQL or similar. |
| In-memory token blacklist | Lost on server restart — logged-out tokens become valid again. Use Redis or a DB-backed blacklist. |
| No breached password check | Minimum 8 characters is enforced but compromised passwords are not checked. Integrate HaveIBeenPwned API before production. |
| Permissive CORS | `allow_origins=["*"]` — set to your specific frontend origin before production. |
| Single worker | JSON storage is not safe for multiple concurrent uvicorn workers. |
| No HTTPS | Run behind a TLS-terminating reverse proxy (nginx, AWS ALB) in production. |

---

## Development Notes

### Atomic writes

`JsonFileStorage` uses `write-to-tmp → os.replace()` for atomic file updates. This prevents partial writes but does not handle concurrent access from multiple processes.

### Correlation IDs

Every request gets a UUID4 correlation ID. It appears in all log lines for that request and is returned as the `X-Correlation-ID` response header. Useful for tracing requests in logs.

### Structured logging

All logs are emitted as JSON lines to stdout. Example:

```json
{"timestamp": "2025-01-01T10:00:00Z", "level": "INFO", "message": "task_created", "task_id": "abc123", "caller_id": "user-uuid", "correlation_id": "req-uuid"}
```

### Hypothesis profiles

Property-based tests use [Hypothesis](https://hypothesis.readthedocs.io/). Two profiles are configured in `pyproject.toml`:

- `ci` — 200 examples per property (default, used in CI)
- `dev` — 50 examples per property (faster for local iteration)

```bash
python -m pytest tests/pbt/ --hypothesis-profile=dev
```

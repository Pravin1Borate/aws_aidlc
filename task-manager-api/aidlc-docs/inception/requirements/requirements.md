# Requirements Document

## Intent Analysis Summary

| Field | Value |
|---|---|
| **User Request** | Build a REST API for task management with user authentication, task CRUD operations, priority levels, and due date tracking |
| **Request Type** | New Project (Greenfield) |
| **Scope Estimate** | Multiple Components — Authentication service + Task management service |
| **Complexity Estimate** | Moderate — REST API with JWT auth, CRUD, priority/status/due-date management, categories & tags, user assignment |
| **Requirements Depth** | Standard |

---

## Technical Stack Decisions

| Concern | Decision | Rationale |
|---|---|---|
| **Language** | Python 3.11+ | User selected |
| **Framework** | FastAPI | High-performance async REST framework, auto-generates OpenAPI docs |
| **Data Storage** | JSON file-based (flat file) | User specified — suitable for local development / small scale |
| **Authentication** | JWT (JSON Web Tokens) | Stateless, ideal for REST APIs; user selected |
| **PBT Framework** | Hypothesis | Mature Python PBT framework (per PBT-09 — Python project) |
| **Deployment** | Local development only | User specified |

---

## Functional Requirements

### FR-01: User Authentication

| ID | Requirement |
|---|---|
| FR-01.1 | Users can register with email address and password |
| FR-01.2 | Users can log in with email and password to receive a JWT access token |
| FR-01.3 | JWT tokens must be validated server-side on every protected request (signature, expiration, issuer) |
| FR-01.4 | Users can log out (client-side token discard; server-side token blacklist optional) |
| FR-01.5 | Passwords must be hashed using an adaptive algorithm (bcrypt or argon2) — never stored in plain text |
| FR-01.6 | All authenticated endpoints return 401 Unauthorized for missing or invalid tokens |

### FR-02: Task CRUD Operations

| ID | Requirement |
|---|---|
| FR-02.1 | Authenticated users can create a new task with: title (required), description (optional), priority, status, due date, assignee, category, tags |
| FR-02.2 | Authenticated users can retrieve a single task by ID (with ownership/permission check) |
| FR-02.3 | Authenticated users can retrieve a list of tasks with optional filtering |
| FR-02.4 | Authenticated users can update a task they own or are assigned to |
| FR-02.5 | Authenticated users can delete a task they own |
| FR-02.6 | Task IDs must be unique and system-generated (UUID) |

### FR-03: Priority Levels

| ID | Requirement |
|---|---|
| FR-03.1 | Tasks support three priority levels: `low`, `medium`, `high` |
| FR-03.2 | Priority is optional on creation; defaults to `medium` if not specified |
| FR-03.3 | Priority can be updated via PATCH/PUT on a task |

### FR-04: Task Status

| ID | Requirement |
|---|---|
| FR-04.1 | Tasks support three statuses: `todo`, `in_progress`, `done` |
| FR-04.2 | New tasks default to `todo` status |
| FR-04.3 | Status can be updated independently of other task fields |

### FR-05: Due Date Tracking

| ID | Requirement |
|---|---|
| FR-05.1 | Tasks support an optional due date (ISO 8601 date format) |
| FR-05.2 | Due dates can be set, updated, or cleared |
| FR-05.3 | Due date must be a valid date (not in the past on creation — validation warning, not blocking) |

### FR-06: Task Assignment

| ID | Requirement |
|---|---|
| FR-06.1 | Tasks can be assigned to any registered user via user ID or email |
| FR-06.2 | The task creator is the default owner |
| FR-06.3 | The assignee and the creator can both read and update the task |
| FR-06.4 | Only the creator (owner) can delete the task |
| FR-06.5 | Assignment can be changed or cleared by the owner |

### FR-07: Categories

| ID | Requirement |
|---|---|
| FR-07.1 | Each task can have one category (single-value, user-defined string) |
| FR-07.2 | Category is optional; tasks without a category are uncategorized |
| FR-07.3 | Category can be updated or removed |

### FR-08: Tags

| ID | Requirement |
|---|---|
| FR-08.1 | Each task can have multiple tags (list of user-defined strings) |
| FR-08.2 | Tags are optional; tasks can have zero or more tags |
| FR-08.3 | Tags can be added, replaced, or removed |

### FR-09: Filtering and Sorting

| ID | Requirement |
|---|---|
| FR-09.1 | Task list endpoint supports filtering by: `status`, `priority`, `due_date` (on or before a given date) |
| FR-09.2 | Filtering parameters are optional — no filter returns all accessible tasks |
| FR-09.3 | Results are sorted by due date ascending by default (tasks without due date appear last) |

### FR-10: Rate Limiting

| ID | Requirement |
|---|---|
| FR-10.1 | All API endpoints must implement rate limiting per user/IP to satisfy SECURITY-11 |
| FR-10.2 | Recommended limit: 100 requests/minute per authenticated user; 20 requests/minute per unauthenticated IP |
| FR-10.3 | Rate limit exceeded must return HTTP 429 Too Many Requests with a Retry-After header |

---

## Non-Functional Requirements

### NFR-01: Performance
- API response time target: < 200ms for typical CRUD operations (local dev, JSON file storage)
- No concurrent write locking required for MVP (single-process, local dev)

### NFR-02: Security
- All endpoints default to authenticated (deny by default) — public endpoints explicitly marked
- Input validation on all API parameters (type, length, format — per SECURITY-05)
- Passwords hashed with bcrypt or argon2 — never plain text (per SECURITY-12)
- JWTs validated server-side on every request — signature, expiration, audience, issuer (per SECURITY-08)
- CORS restricted to explicitly allowed origins (per SECURITY-08)
- Structured logging with no PII or tokens in logs (per SECURITY-03)
- Global error handler with generic user-facing messages — no stack traces (per SECURITY-09, SECURITY-15)
- Object-level authorization: every resource access verifies caller's ownership or permission (per SECURITY-08)
- Rate limiting on all endpoints (per SECURITY-11 and FR-10)
- Dependencies pinned in requirements.txt / lock file (per SECURITY-10)

### NFR-03: Testing
- Unit tests for all business logic (pytest)
- Integration tests for all API endpoints
- Property-based tests using Hypothesis for:
  - JWT token round-trips
  - Task model invariants (status/priority validation)
  - Input serialization/deserialization (round-trip properties)
  - Idempotency of PUT/DELETE endpoints
- PBT framework: Hypothesis (per PBT-09)
- Both example-based and property-based tests required (per PBT-10)

### NFR-04: Data Storage
- JSON file-based persistence (flat file, local filesystem)
- Data file location: configurable via environment variable (default: `data/tasks.json`, `data/users.json`)
- File reads/writes use atomic operations to prevent corruption
- Backup of data files is manual (no automated backup for local dev)

### NFR-05: Code Quality
- Full type annotations (Python type hints + Pydantic models)
- OpenAPI/Swagger documentation auto-generated by FastAPI
- Environment-based configuration (`.env` file + python-dotenv or FastAPI settings)
- No hardcoded secrets or credentials in source code (per SECURITY-12)

### NFR-06: Observability
- Structured logging (JSON format) for all requests: timestamp, request ID, log level, message (per SECURITY-03)
- Log level configurable via environment variable
- No sensitive data (passwords, tokens, PII) in logs
- Health check endpoint (`GET /health`) returning service status

---

## Extension Configuration Summary

| Extension | Status | Notes |
|---|---|---|
| Security Baseline (15 rules) | **ENABLED** | All rules enforced as blocking constraints |
| Resiliency Baseline (15 rules) | **ENABLED** | Most rules N/A for local dev scope (see below) |
| Property-Based Testing (10 rules) | **ENABLED** | All rules enforced as blocking constraints |

### Resiliency Baseline — Applicability for Local Dev

| Rule | Status | Rationale |
|---|---|---|
| RESILIENCY-01 | Applicable | Document workload criticality |
| RESILIENCY-02 | Applicable | RTO/RPO: Hours (Backup & Restore); local dev backup |
| RESILIENCY-03 | N/A | Local dev; exempt from formal change management |
| RESILIENCY-04 | Applicable | CI/CD to be determined in NFR Design phase |
| RESILIENCY-05 | Applicable (minimal) | Structured logging and health check endpoint |
| RESILIENCY-06 | Applicable | Health check endpoint required |
| RESILIENCY-07 | N/A | No cloud resiliency assessment tooling for local dev |
| RESILIENCY-08 | N/A | Local dev only; no multi-zone/multi-region needed |
| RESILIENCY-09 | N/A | Local dev; no cloud auto-scaling |
| RESILIENCY-10 | Applicable | Timeouts and graceful degradation for file I/O |
| RESILIENCY-11 | Applicable (minimal) | Backup & Restore — manual file backup documented |
| RESILIENCY-12 | Applicable (minimal) | Manual backup process documented for data files |
| RESILIENCY-13 | Applicable (minimal) | Basic recovery runbook for data file restoration |
| RESILIENCY-14 | N/A | Local dev; chaos engineering deferred |
| RESILIENCY-15 | N/A | Local dev; no production incident response needed |

---

## API Endpoints Summary

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Register a new user | Public |
| POST | `/auth/login` | Authenticate and get JWT | Public |
| POST | `/auth/logout` | Logout (token invalidation) | Required |
| GET | `/tasks` | List tasks (with filters) | Required |
| POST | `/tasks` | Create a new task | Required |
| GET | `/tasks/{id}` | Get a task by ID | Required |
| PUT | `/tasks/{id}` | Replace a task (full update) | Required |
| PATCH | `/tasks/{id}` | Partial update a task | Required |
| DELETE | `/tasks/{id}` | Delete a task | Required |
| GET | `/users` | List all users (for assignment) | Required |
| GET | `/users/{id}` | Get user profile | Required |
| GET | `/health` | Health check | Public |

---

## Data Models

### User
```
id: UUID (system-generated)
email: string (unique, required)
password_hash: string (bcrypt/argon2)
full_name: string (optional)
created_at: datetime
updated_at: datetime
```

### Task
```
id: UUID (system-generated)
title: string (required, max 255 chars)
description: string (optional, max 2000 chars)
status: enum [todo, in_progress, done] (default: todo)
priority: enum [low, medium, high] (default: medium)
due_date: date (optional, ISO 8601)
category: string (optional, max 100 chars)
tags: list[string] (optional, each tag max 50 chars)
owner_id: UUID (set to creator on creation)
assignee_id: UUID (optional, any registered user)
created_at: datetime
updated_at: datetime
```

---

## Constraints and Assumptions

1. JSON file storage is for local development only — production migration to a real database is out of scope
2. No email verification on registration (local dev assumption)
3. JWT secret key stored in environment variable (not hardcoded)
4. Single-process application — no distributed state or concurrency concerns
5. No admin roles in MVP — all authenticated users have equal base permissions (ownership-based access)
6. Pagination on list endpoints is optional for MVP (may add offset/limit params)

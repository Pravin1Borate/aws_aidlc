# Integration Test Instructions — Task Manager API

## Overview

Integration tests exercise the full HTTP stack using FastAPI's `TestClient`. They start the actual application (including middleware, DI, and JSON storage) against an isolated temp directory. No external services are required.

**Test runner**: pytest  
**HTTP client**: httpx via `TestClient` (synchronous)  
**Storage isolation**: each test function gets a fresh `tmp_path` via pytest fixture

---

## Prerequisites

```bash
pip install -r requirements-dev.txt
# .env must exist with JWT_SECRET_KEY set
```

---

## Run All Integration Tests

```bash
python -m pytest tests/integration/ -v
```

---

## Run Integration Tests by Feature

```bash
# Auth endpoints (Unit 1)
python -m pytest tests/integration/auth/ -v

# Task endpoints (Unit 2)
python -m pytest tests/integration/tasks/test_task_endpoints.py -v

# User endpoints (Unit 2)
python -m pytest tests/integration/tasks/test_user_endpoints.py -v
```

---

## Integration Test Inventory

### Unit 1 ↔ Unit 2 Integration Scenarios

The integration tests in `tests/integration/tasks/` implicitly test the cross-unit integration:

| Scenario | Test File | Description |
|---|---|---|
| JWT auth → Task creation | `test_task_endpoints.py::TestCreateTask` | Token from `/auth/login` used to create a task via `POST /tasks` |
| User registration → User read | `test_user_endpoints.py::TestListUsers` | User registered via `/auth/register` appears in `GET /users` (same `users.json`) |
| Assignee resolution | `test_task_endpoints.py` (create with assignee_email) | Registered user's email used to assign a task |
| Token invalidation → Task denial | Covered by `TestAuthEnforcement` classes | Unauthenticated requests get 401 across all task/user routes |

### Unit 1: Auth Endpoint Tests (`tests/integration/auth/test_auth_endpoints.py`)

| Test Class | Count | Covers |
|---|---|---|
| `TestRegister` | 4 | success, duplicate email, weak password, invalid email |
| `TestLogin` | 4 | success, wrong password, unknown user, account lockout |
| `TestLogout` | 3 | success, reuse of blacklisted token |
| `TestMe` | 3 | success, expired token, blacklisted token |
| `TestHealthEndpoints` | 2 | liveness, readiness |

### Unit 2: Task Endpoint Tests (`tests/integration/tasks/test_task_endpoints.py`)

| Test Class | Count | Covers |
|---|---|---|
| `TestAuthEnforcement` | 6 | All 6 task endpoints return 401 without token |
| `TestCreateTask` | 4 | minimal, full fields, missing title (422), invalid status (422) |
| `TestGetTask` | 3 | by id, 404, any-auth-user-can-read |
| `TestListTasks` | 5 | paginated shape, filter by status, filter by priority, pagination params, soft-deleted excluded |
| `TestUpdateTask` | 3 | owner full update, unrelated user 403, 404 |
| `TestPatchTask` | 2 | preserve unchanged fields, tag merge |
| `TestDeleteTask` | 3 | owner deletes (204), deleted → 404, non-owner 403 |

### Unit 2: User Endpoint Tests (`tests/integration/tasks/test_user_endpoints.py`)

| Test Class | Count | Covers |
|---|---|---|
| `TestAuthEnforcement` | 2 | Both user endpoints return 401 |
| `TestListUsers` | 2 | returns registered users, no sensitive fields |
| `TestGetUser` | 3 | by id, 404, cross-user read |

---

## Key Integration Scenarios (Manual Verification)

### Scenario 1: Full Task Lifecycle

```bash
# Start the server
python -m uvicorn src.main:app --reload

# 1. Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Password1","full_name":"Alice"}'

# 2. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Password1"}'
# Save the access_token from response

# 3. Create task
curl -X POST http://localhost:8000/tasks/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy groceries","priority":"high","due_date":"2025-12-31","tags":["shopping"]}'

# 4. List tasks
curl http://localhost:8000/tasks/ \
  -H "Authorization: Bearer <token>"

# 5. Patch task
curl -X PATCH http://localhost:8000/tasks/<task_id> \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status":"done","tags":["done"],"tags_remove":["shopping"]}'

# 6. Delete task
curl -X DELETE http://localhost:8000/tasks/<task_id> \
  -H "Authorization: Bearer <token>"

# 7. Verify deleted (should return 404)
curl http://localhost:8000/tasks/<task_id> \
  -H "Authorization: Bearer <token>"
```

### Scenario 2: Cross-Unit User Assignment

```bash
# Register owner and assignee
# Login as owner → get owner_token
# Login as assignee → get assignee_token

# Get assignee's user_id
curl http://localhost:8000/users/ -H "Authorization: Bearer <owner_token>"

# Create task assigned to assignee
curl -X POST http://localhost:8000/tasks/ \
  -H "Authorization: Bearer <owner_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Review PR","assignee_email":"assignee@example.com"}'

# Assignee can update the task
curl -X PATCH http://localhost:8000/tasks/<task_id> \
  -H "Authorization: Bearer <assignee_token>" \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}'

# Assignee CANNOT delete (should return 403)
curl -X DELETE http://localhost:8000/tasks/<task_id> \
  -H "Authorization: Bearer <assignee_token>"
```

---

## Health Check Verification

```bash
curl http://localhost:8000/health/live    # Always 200
curl http://localhost:8000/health/ready   # 200 if JWT configured + data dir writable
```

---

## Troubleshooting

### Tests pass locally but fail in sequence
The `client` fixture is function-scoped — each test gets a clean DB. If tests share state, check that `clear_token_blacklist` autouse fixture is working.

### 401 responses on authenticated endpoints
Check that the `patch_settings` fixture is in the fixture chain — it sets `JWT_SECRET_KEY`.

### JSON decode errors on responses
The `TestClient` returns proper JSON — use `resp.json()` not `resp.text`.

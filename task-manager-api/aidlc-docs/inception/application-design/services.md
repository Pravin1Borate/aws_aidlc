# Services

## Service Layer Overview

The service layer sits between routers (HTTP concerns) and repositories (data concerns). Services own all business logic, enforce authorization rules, and coordinate across repositories when needed.

```
HTTP Request
    │
    ▼
Router (validate shape, extract params, return HTTP response)
    │
    ▼
Service (business logic, authorization, cross-repo coordination)
    │
    ▼
Repository (data I/O only, no business logic)
    │
    ▼
JsonFileStorage (atomic file read/write)
```

---

## AuthService

**Package**: `auth/service.py`

**Responsibilities**:
- Orchestrate user registration: check uniqueness, hash password, persist user
- Orchestrate login: verify credentials, issue signed JWT
- Orchestrate logout: validate token, add to blacklist
- Provide current-user resolution for the `get_current_user` FastAPI dependency

**Coordinates with**:
- `UserRepository` — user lookup and persistence
- `SecurityUtils` — password hashing/verification, JWT creation/decoding, blacklist management

**Business rules enforced** (detail in Functional Design):
- Email uniqueness on registration
- Credential verification on login (constant-time comparison)
- Token blacklist check on every protected request
- Token expiry enforcement

**Does NOT**:
- Handle HTTP request/response objects (that is the Router's concern)
- Write directly to files (that is the Repository's concern)

---

## TaskService

**Package**: `tasks/service.py`

**Responsibilities**:
- Orchestrate all task lifecycle operations: create, read, update, delete
- Enforce task access control: ownership (create, full update, delete) and assignment (partial update, read)
- Apply task filtering: status, priority, due date
- Validate assignee existence by coordinating with UserRepository

**Coordinates with**:
- `TaskRepository` — task persistence operations
- `UserRepository` — assignee validation (confirm assignee_id refers to a real user)

**Business rules enforced** (detail in Functional Design):
- Owner-only: full update (PUT), delete
- Owner or assignee: read, partial update (PATCH)
- Assignee validation before saving
- Default values: status=todo, priority=medium on creation
- Filter composition: all provided filters applied as AND conditions

**Does NOT**:
- Handle HTTP request/response objects
- Write directly to files

---

## UserService

**Package**: `users/service.py`

**Responsibilities**:
- Provide read-only access to the user list for assignee selection
- Strip sensitive fields (password hashes) from user records before returning

**Coordinates with**:
- `UserRepository` — user listing

**Business rules enforced**:
- Password hashes are never returned in any response
- Only public user fields exposed: id, email, full_name

**Does NOT**:
- Support user creation or modification (owned by AuthService)

---

## Service Interaction Summary

| Caller | Calls Service | Calls Repository | Notes |
|---|---|---|---|
| AuthRouter | AuthService | — | AuthService → UserRepository |
| TaskRouter | TaskService | — | TaskService → TaskRepository + UserRepository |
| UserRouter | UserService | — | UserService → UserRepository (read-only) |
| `get_current_user` dep | AuthService.get_current_user | — | Validates token on every protected request |

---

## Cross-Service Coordination Rules

1. **No service calls another service directly.** Cross-feature data needs (e.g., TaskService needing User data) are satisfied by injecting the required Repository, not by calling the other feature's Service.

2. **Services are stateless.** No instance state is held between requests; all state lives in the Repository/Storage layer.

3. **Services raise typed exceptions.** `NotFoundError`, `ForbiddenError`, `UnauthorizedError`, `ConflictError` are raised by services and caught by the global error handlers registered on the app.

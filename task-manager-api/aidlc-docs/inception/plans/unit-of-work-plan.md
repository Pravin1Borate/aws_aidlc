# Unit of Work Plan

## Context Assessment

Units were pre-identified during Workflow Planning and confirmed by Application Design.
No clarifying questions are required — all unit boundaries, dependencies, and story assignments
are unambiguous given the current context.

**Unit count**: 2
**Deployment model**: Monolith (single FastAPI application, logical separation by feature package)
**Development sequence**: Sequential — Unit 1 must be complete before Unit 2 begins (Unit 2 depends on Unit 1's JWT middleware and UserRepository)

---

## Units of Work

### Unit 1: Authentication
**Package scope**: `auth/`, `core/security.py`, `core/errors.py`, `core/logging.py`, `config.py`, `dependencies.py`, `main.py` (bootstrap)
**Stories**: US-01, US-02, US-03, US-04
**Delivers**: User registration, login, JWT issuance, logout/blacklist, `get_current_user` FastAPI dependency, password hashing, structured logging, global error handlers

### Unit 2: Task Management
**Package scope**: `tasks/`, `users/`, `core/rate_limiter.py`, `core/storage.py` (full implementation)
**Stories**: US-05 through US-22
**Delivers**: Full task CRUD, priority/status/due-date/category/tags, user assignment, filtering, user discovery endpoints, rate limiting, health endpoint
**Depends on**: Unit 1 (JWT middleware + UserRepository)

---

## Artifacts to Generate

- [x] `aidlc-docs/inception/application-design/unit-of-work.md`
  - [x] Unit 1 definition, scope, responsibilities, deliverables
  - [x] Unit 2 definition, scope, responsibilities, deliverables
  - [x] Code organisation strategy (by-feature monolith)
- [x] `aidlc-docs/inception/application-design/unit-of-work-dependency.md`
  - [x] Dependency matrix between units
  - [x] Development sequence with rationale
  - [x] Shared component usage map
- [x] `aidlc-docs/inception/application-design/unit-of-work-story-map.md`
  - [x] All 22 stories assigned to units
  - [x] Story-to-component mapping within each unit

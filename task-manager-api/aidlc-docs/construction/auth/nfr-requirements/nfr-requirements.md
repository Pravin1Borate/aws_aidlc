# NFR Requirements — Unit 1: Authentication

## Performance

| ID | Requirement | Target | Rationale |
|---|---|---|---|
| PERF-AUTH-01 | Registration endpoint response time | < 800ms (P95) | bcrypt cost-12 hashing takes ~200–400ms; includes I/O |
| PERF-AUTH-02 | Login endpoint response time (success path) | < 800ms (P95) | bcrypt verify is the bottleneck; acceptable for local dev |
| PERF-AUTH-03 | Login endpoint response time (lockout fast path) | < 50ms | Lockout check happens before bcrypt — no hashing needed |
| PERF-AUTH-04 | Token validation (get_current_user) response overhead | < 5ms | In-memory JWT decode + blacklist set lookup; must be negligible |
| PERF-AUTH-05 | Logout endpoint response time | < 50ms | Token decode + in-memory set insertion |

**Note**: bcrypt cost factor 12 is intentionally slow (~200–400ms). This is a security property, not a bug. SLAs must account for it.

---

## Availability

| ID | Requirement | Detail |
|---|---|---|
| AVAIL-AUTH-01 | Liveness health check | `GET /health/live` — returns `{"status": "ok", "service": "task-manager-api"}`. Must respond < 10ms. No dependencies checked. |
| AVAIL-AUTH-02 | Readiness health check | `GET /health/ready` — checks: (1) JWT config present and parseable, (2) data directory accessible. Returns `{"status": "ready"\|"degraded", "checks": {...}}` |
| AVAIL-AUTH-03 | Token blacklist availability | In-memory set; always available within process lifetime. Cleared on restart (documented limitation). |
| AVAIL-AUTH-04 | Graceful startup | Application must validate JWT_SECRET_KEY presence at startup; fail fast with clear error if missing. |

---

## Security

| ID | Requirement | Source Rule | Implementation |
|---|---|---|---|
| SEC-AUTH-01 | Rate limiting — unauthenticated endpoints | SECURITY-11 | 20 req/min per IP on `/auth/register`, `/auth/login` via slowapi |
| SEC-AUTH-02 | Rate limiting — authenticated endpoints | SECURITY-11 | 100 req/min per user on `/auth/logout`, `/auth/me` via slowapi |
| SEC-AUTH-03 | Password hashing | SECURITY-12 | bcrypt, cost factor 12, never stored in plain text |
| SEC-AUTH-04 | Account lockout | SECURITY-12 | 5 consecutive failures → 15-minute lockout, counter stored in users.json |
| SEC-AUTH-05 | JWT signing | SECURITY-12 | HS256, JWT_SECRET_KEY from environment (never hardcoded) |
| SEC-AUTH-06 | Sensitive config never hardcoded | SECURITY-09 | pydantic-settings + `.env` file; `.env` in `.gitignore` |
| SEC-AUTH-07 | Generic error responses | SECURITY-09 | No stack traces in API responses; all 401s return generic messages |
| SEC-AUTH-08 | Structured access logging | SECURITY-03 | JSON log line per request: method, path, status, duration, user_id |
| SEC-AUTH-09 | Breached password check | SECURITY-12 | **SKIPPED** — documented known gap, local dev PoC only |

---

## Reliability

| ID | Requirement | Detail |
|---|---|---|
| REL-AUTH-01 | Global exception handler | All unhandled exceptions caught by FastAPI exception handler; 500 returned with generic message; full details logged (never exposed) |
| REL-AUTH-02 | JSON file write safety | Atomic write pattern (write-to-temp → rename) prevents partial writes corrupting users.json |
| REL-AUTH-03 | Startup validation | Fail fast if JWT_SECRET_KEY missing or DATA_DIR unwritable |
| REL-AUTH-04 | Input validation | All request bodies validated by Pydantic v2 models; 422 on validation failure |

---

## Testability

| ID | Requirement | Detail |
|---|---|---|
| TEST-AUTH-01 | Unit test coverage | pytest, minimum 80% line coverage on `auth/` and `core/security.py` |
| TEST-AUTH-02 | Property-based tests | Hypothesis — minimum 6 properties identified in business-logic-model.md (PBT-01 through PBT-06) |
| TEST-AUTH-03 | Test isolation | All tests use tmp_path fixture for JSON files; no shared state between tests |
| TEST-AUTH-04 | Hypothesis configuration | CI profile: max_examples=200; dev profile: max_examples=50 (via pyproject.toml settings) |
| TEST-AUTH-05 | Test markers | pytest markers: `unit`, `integration`, `pbt` — allows selective test execution |

---

## Maintainability

| ID | Requirement | Detail |
|---|---|---|
| MAINT-AUTH-01 | Dependency pinning | `requirements.txt` pinned with exact versions; `requirements-dev.txt` for test/dev tools |
| MAINT-AUTH-02 | Type annotations | All public functions/methods fully type-annotated (mypy-compatible) |
| MAINT-AUTH-03 | Log correlation | Each request gets a correlation ID (UUID) propagated through all log entries |

---

## Extension Compliance Summary

### Security Baseline
| Rule | Status | Notes |
|---|---|---|
| SECURITY-11 (Rate limiting) | Compliant | slowapi, in-memory, 20/100 req/min |
| SECURITY-12 (Auth & credentials) | Partially non-compliant | bcrypt+lockout compliant; breached password check skipped (known gap) |
| SECURITY-03 (Structured logging) | Compliant | python-json-logger, JSON lines |
| SECURITY-09 (Hardening) | Compliant | pydantic-settings, generic errors |
| Others | N/A | Local dev scope — no cloud IAM, network config, or HTML endpoints |

### Resiliency Baseline
| Rule | Status | Notes |
|---|---|---|
| RESILIENCY-04 (Health checks) | Compliant | /health/live + /health/ready |
| RESILIENCY-02 (Backup/Restore) | N/A | Local dev — no cloud storage, RTO/RPO accepted as Backup&Restore tier |
| Others | N/A | Local dev scope — no cloud redundancy, regional topology, or CI/CD pipeline |

### Property-Based Testing
| Rule | Status | Notes |
|---|---|---|
| PBT-01 (Property identification) | Compliant | 6 properties identified in business-logic-model.md |
| PBT-02 (Round-trip) | Compliant | bcrypt hash/verify, JWT create/decode |
| PBT-03 (Invariants) | Compliant | failed_login_attempts, lockout invariant, email normalization |
| PBT-04 (Idempotence) | Compliant | Token blacklist idempotency |
| PBT-05 through PBT-10 | Compliant | Hypothesis profiles configured; generators planned |

# Business Rules — Unit 1: Authentication

## BR-AUTH-01: User Registration

| Rule ID | Rule | Error if violated |
|---|---|---|
| BR-AUTH-01.1 | Email must match a valid email format (RFC 5322) | 422 Unprocessable Entity |
| BR-AUTH-01.2 | Email is normalized to lowercase before storage and uniqueness check | — (processing rule) |
| BR-AUTH-01.3 | Email must be unique across all registered users (case-insensitive) | 409 Conflict — generic message |
| BR-AUTH-01.4 | Password must be at least 8 characters | 422 Unprocessable Entity |
| BR-AUTH-01.5 | Password is hashed with bcrypt (cost factor 12) before storage | — (processing rule) |
| BR-AUTH-01.6 | Plain-text password is never stored, logged, or returned | — (security invariant) |
| BR-AUTH-01.7 | `id` is a system-generated UUID; client cannot supply it | — (processing rule) |
| BR-AUTH-01.8 | `created_at` and `updated_at` are system-set UTC datetimes | — (processing rule) |

> **SECURITY-12 Known Gap**: Breached password check (Have I Been Pwned or equivalent) is **not implemented**.
> **Justification**: Local development scope only; external API dependency not appropriate for this phase.
> **Mitigation**: Minimum 8-character requirement still enforced. This gap must be addressed before any production deployment.
> **SECURITY-12 compliance status**: Partially non-compliant (minimum length enforced; breach check skipped).

---

## BR-AUTH-02: User Login

| Rule ID | Rule | Error if violated |
|---|---|---|
| BR-AUTH-02.1 | Email is normalized to lowercase before lookup | — (processing rule) |
| BR-AUTH-02.2 | If `lockout_until` is set and > now (UTC): reject immediately with 401 | 401 Unauthorized — generic message |
| BR-AUTH-02.3 | User not found by email: return 401 with **identical** response to wrong-password (no user enumeration) | 401 Unauthorized |
| BR-AUTH-02.4 | Password verification uses constant-time comparison (bcrypt verify) | — (security invariant) |
| BR-AUTH-02.5 | Wrong password: increment `failed_login_attempts` by 1 | 401 Unauthorized |
| BR-AUTH-02.6 | If `failed_login_attempts` reaches 5 after increment: set `lockout_until = utcnow() + 15 minutes` | 401 Unauthorized (lockout message) |
| BR-AUTH-02.7 | Correct password: reset `failed_login_attempts` to 0, set `lockout_until = None`, issue JWT | — (success path) |
| BR-AUTH-02.8 | JWT payload must include: `sub` (user UUID as string), `email`, `exp` (UTC expiry), `iat` (issued at) | — (processing rule) |
| BR-AUTH-02.9 | JWT is signed with `JWT_SECRET_KEY` using HS256 algorithm | — (security invariant) |
| BR-AUTH-02.10 | JWT expiry is `utcnow() + JWT_EXPIRY_MINUTES` (default 60 minutes) | — (processing rule) |

### Account Lockout Parameters
| Parameter | Value | Source |
|---|---|---|
| Failure threshold | 5 consecutive failures | Hard-coded constant |
| Lockout duration | 15 minutes | Hard-coded constant |
| Counter reset trigger | Successful login | — |
| Lockout expiry check | `lockout_until > utcnow()` | Evaluated on every login attempt |

---

## BR-AUTH-03: Token Validation (`get_current_user`)

| Rule ID | Rule | Error if violated |
|---|---|---|
| BR-AUTH-03.1 | Authorization header must be present in format `Bearer <token>` | 401 Unauthorized |
| BR-AUTH-03.2 | JWT signature must be valid (verified with `JWT_SECRET_KEY`) | 401 Unauthorized |
| BR-AUTH-03.3 | JWT must not be expired (`exp` claim > utcnow()) | 401 Unauthorized |
| BR-AUTH-03.4 | Token must not be in the blacklist | 401 Unauthorized |
| BR-AUTH-03.5 | `sub` claim must correspond to an existing user | 401 Unauthorized |
| BR-AUTH-03.6 | All validation steps run on **every** protected request (never cached) | — (security invariant) |
| BR-AUTH-03.7 | Response to any validation failure is always HTTP 401 (no indication of which check failed) | — (security invariant) |

---

## BR-AUTH-04: Logout

| Rule ID | Rule | Error if violated |
|---|---|---|
| BR-AUTH-04.1 | Token must pass full validation (BR-AUTH-03.1 through BR-AUTH-03.5) before blacklisting | 401 Unauthorized |
| BR-AUTH-04.2 | Valid token is added to the in-memory blacklist | — (processing rule) |
| BR-AUTH-04.3 | Adding an already-blacklisted token is a no-op (idempotent) | — (idempotency invariant) |
| BR-AUTH-04.4 | After successful logout, the same token returns 401 on any subsequent protected request | — (security invariant) |

---

## Security Compliance Summary (SECURITY Extension)

| Rule | Status | Notes |
|---|---|---|
| SECURITY-01 (Encryption at rest) | N/A | Local file storage; no cloud key management applicable |
| SECURITY-02 (Access logging on network intermediaries) | N/A | No load balancer or API gateway (local dev) |
| SECURITY-03 (Structured logging) | Compliant | JSON structured logger configured in `core/logging.py` |
| SECURITY-04 (HTTP security headers) | N/A | REST API only, no HTML endpoints |
| SECURITY-05 (Input validation) | Compliant | Pydantic models validate all inputs |
| SECURITY-06 (Least-privilege IAM) | N/A | No cloud IAM (local dev) |
| SECURITY-07 (Network config) | N/A | No cloud network resources (local dev) |
| SECURITY-08 (App-level access control) | Compliant | `get_current_user` dependency + JWT validation on every request |
| SECURITY-09 (Security hardening) | Compliant | Global error handlers return generic messages; no stack traces |
| SECURITY-10 (Supply chain) | Compliant | Dependencies pinned in requirements.txt with lock file |
| SECURITY-11 (Rate limiting) | Compliant | RateLimiterMiddleware on all endpoints (Unit 2 scope) |
| SECURITY-12 (Auth & credential mgmt) | **Partially non-compliant** | Bcrypt hashing compliant; account lockout compliant; **breached password check skipped** (known gap, local dev PoC) |
| SECURITY-13 (Software/data integrity) | Compliant | No unsafe deserialization; atomic file writes |
| SECURITY-14 (Alerting & monitoring) | N/A | Local dev; no cloud log groups or alert routing |
| SECURITY-15 (Exception handling) | Compliant | Global error handler + try/finally in repositories |

# NFR Requirements Plan — Unit 1: Authentication

## Plan Execution Checklist

- [x] Analyze functional design artifacts
- [x] Ask clarifying questions on ambiguous NFR decisions
- [x] Generate `nfr-requirements.md`
- [x] Generate `tech-stack-decisions.md`

---

## Context Already Established (No Questions Needed)

From requirements.md and extension configs:
- Python 3.11+ / FastAPI — locked
- JSON file storage — locked
- JWT authentication — locked
- Hypothesis for PBT — locked
- Security, Resiliency, PBT extensions — all enabled
- Scale: local dev, small scale, single process

---

## Questions Requiring User Input

### Q1: Password hashing library selection (SECURITY-12)

bcrypt and argon2-cffi are both valid choices for Python. Which should be used?

A) **bcrypt** (`bcrypt` library) — battle-tested, widely used, passlib wrapper available.
   Cost factor 12. Slower key derivation than argon2 but very widely deployed.

B) **argon2-cffi** — Argon2id algorithm, recommended by OWASP as the preferred modern
   KDF. Memory-hard (harder to GPU-crack), slightly more complex to configure.

C) Either — let the AI choose based on security extension requirements.

[Answer]: A

---

### Q2: Rate limiter implementation (FR-10 / SECURITY-11)

The security extension mandates rate limiting (100 req/min authenticated, 20 req/min
unauthenticated by IP). Which approach for Unit 1?

A) **slowapi** — FastAPI-native library, decorator-based rate limiting, minimal code.
   Uses in-memory storage (acceptable for local dev single process).

B) **Custom ASGI middleware** — hand-rolled middleware using a token-bucket or sliding
   window algorithm. More control, zero new dependencies, but more code.

C) **starlette-limiter or limits library** — another third-party option with flexible
   backend support (in-memory, Redis, etc.).

[Answer]: A

---

### Q3: JWT library selection

A) **python-jose** — widely used, supports RS256/HS256, has known CVEs in older versions
   but current versions are maintained. Well-documented with FastAPI tutorials.

B) **PyJWT** — lighter, maintained by jwt.io, fewer known vulnerabilities. Simpler API.
   Actively maintained. OWASP recommends keeping JWT libraries minimal.

C) Either — let the AI choose based on security best practices.

[Answer]: A

---

### Q4: Structured logging format (SECURITY-03 / RESILIENCY)

The security extension requires structured logging. Which format for log output?

A) **JSON lines** (one JSON object per line) — machine-readable, easy to pipe to
   log aggregators later. Slightly harder to read in terminal during dev.

B) **Human-readable structured** — colored key=value format (e.g., structlog's
   dev renderer) during development, with JSON as the production target.

C) **Standard Python logging with JSON formatter** — use stdlib logging + a JSON
   formatter (e.g., `python-json-logger`). Familiar pattern, minimal dependencies.

[Answer]: C

---

### Q5: Health check endpoint (RESILIENCY-04)

RESILIENCY-04 requires a health check endpoint. Scope for Unit 1?

A) **Liveness only** — `GET /health` returns `{"status": "ok"}`. Confirms process is
   running. No dependency checks (storage check belongs to Unit 2).

B) **Liveness + readiness** — `GET /health/live` (process up) and `GET /health/ready`
   (JWT config valid, data directory accessible). Slightly more setup but production-ready pattern.

C) **Skip for Unit 1** — add health check in Unit 2 once storage layer exists,
   since a meaningful readiness check needs storage access.

[Answer]: B

---

### Q6: Test configuration — pytest settings

A) **pytest.ini or pyproject.toml** — single config file approach. All test settings
   (Hypothesis profiles, markers, coverage) in one place.

B) **conftest.py only** — minimal config in pyproject.toml, all fixtures and settings
   in conftest.py. More Pythonic for smaller projects.

[Answer]: A

---

### Q7: Environment configuration (SECURITY-09)

Sensitive settings (JWT_SECRET_KEY) must never be hardcoded. Which approach?

A) **pydantic-settings with `.env` file** — `BaseSettings` reads from `.env` 
   automatically. Type-safe, validated, standard FastAPI pattern.

B) **python-dotenv + manual loading** — explicit `load_dotenv()` call with `os.getenv`.
   More control, fewer abstractions.

[Answer]: A


# Tech Stack Decisions — Unit 1: Authentication

## Runtime

| Component | Decision | Version | Rationale |
|---|---|---|---|
| Language | Python | 3.11+ | Locked in requirements |
| Web framework | FastAPI | ^0.111 | Locked in requirements; async, Pydantic v2 native |
| ASGI server | uvicorn | ^0.30 | Standard FastAPI dev server |

---

## Authentication & Security Libraries

| Component | Decision | Library | Version | Rationale |
|---|---|---|---|---|
| Password hashing | bcrypt | `bcrypt` | ^4.1 | User choice Q1=A. Battle-tested, widely deployed, cost factor 12 |
| JWT encoding/decoding | python-jose | `python-jose[cryptography]` | ^3.3 | User choice Q3=A. HS256 support, FastAPI tutorial standard |
| Rate limiting | slowapi | `slowapi` | ^0.1 | User choice Q2=A. FastAPI-native, decorator-based, in-memory for local dev |
| Environment config | pydantic-settings | `pydantic-settings` | ^2.0 | User choice Q7=A. Type-safe, validated, BaseSettings from .env |

**Security note on python-jose**: Ensure version >= 3.3.0 to avoid known CVEs. Pin exact version in requirements.txt.

---

## Logging

| Component | Decision | Library | Version | Rationale |
|---|---|---|---|---|
| Structured logging | JSON formatter | `python-json-logger` | ^2.0 | User choice Q4=C. stdlib logging + JSON formatter. Minimal deps, familiar pattern. |
| Log format | JSON lines | — | — | One JSON object per line. Machine-readable, easy to redirect to log aggregators |

### Log entry schema
```json
{
  "timestamp": "2026-06-29T14:22:00.123Z",
  "level": "INFO",
  "message": "HTTP request",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "path": "/auth/login",
  "status_code": 200,
  "duration_ms": 312,
  "user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

---

## Testing Stack

| Component | Decision | Library | Version | Rationale |
|---|---|---|---|---|
| Test runner | pytest | `pytest` | ^8.0 | Standard Python testing |
| PBT framework | Hypothesis | `hypothesis` | ^6.100 | Locked in requirements |
| HTTP test client | httpx | `httpx` | ^0.27 | FastAPI TestClient uses httpx under the hood |
| Coverage | pytest-cov | `pytest-cov` | ^5.0 | Coverage reports with pytest integration |
| Async test support | anyio | `anyio[trio]` | ^4.0 | For testing async FastAPI routes |
| Config file | pyproject.toml | — | — | User choice Q6=A. Unified config: pytest, coverage, Hypothesis, mypy |

---

## pyproject.toml Configuration Outline

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: unit tests",
    "integration: integration tests",
    "pbt: property-based tests (Hypothesis)",
]
addopts = "--cov=src --cov-report=term-missing"

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "*/conftest.py"]

[tool.coverage.report]
fail_under = 80

[tool.hypothesis]
suppress_health_check = ["too_slow"]
deriving_default_profile = "ci"

[tool.hypothesis.profiles.ci]
max_examples = 200

[tool.hypothesis.profiles.dev]
max_examples = 50
```

---

## Health Check Endpoints

User choice Q5=B — Liveness + Readiness:

| Endpoint | Method | Response | Checks |
|---|---|---|---|
| `/health/live` | GET | `{"status": "ok", "service": "task-manager-api"}` | Process is running (no deps) |
| `/health/ready` | GET | `{"status": "ready"\|"degraded", "checks": {"jwt_config": bool, "data_dir": bool}}` | JWT_SECRET_KEY present, data dir accessible |

Both endpoints are **unauthenticated** and **excluded from rate limiting**.

---

## Full requirements.txt (Unit 1 scope)

```
# Runtime
fastapi==0.111.1
uvicorn[standard]==0.30.1
pydantic==2.7.4
pydantic-settings==2.3.4

# Auth & Security
bcrypt==4.1.3
python-jose[cryptography]==3.3.0
slowapi==0.1.9

# Logging
python-json-logger==2.0.7
```

## Full requirements-dev.txt (Unit 1 scope)

```
# Testing
pytest==8.2.2
pytest-cov==5.0.0
hypothesis==6.104.2
httpx==0.27.0
anyio[trio]==4.4.0

# Type checking
mypy==1.10.0
```

---

## Environment Variables (.env.example)

```dotenv
# Required — generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=your-secret-key-here

# Optional — defaults shown
JWT_EXPIRY_MINUTES=60
DATA_DIR=./data
LOG_LEVEL=INFO
```

`.env` must be in `.gitignore`. Never commit actual secrets.

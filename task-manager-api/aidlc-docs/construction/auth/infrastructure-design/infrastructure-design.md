# Infrastructure Design — Unit 1: Authentication

## Deployment Target

**Environment**: Local development only
**Scale**: Single developer, single process, no concurrent load
**Cloud**: None — all components run on developer machine

---

## Compute

| Component | Technology | Configuration |
|---|---|---|
| Web server | uvicorn | `--host APP_HOST --port APP_PORT --reload` |
| Application | FastAPI (single process) | Single uvicorn worker (default) |
| Run mode | uvicorn directly | No Docker, no process manager |

**Start command**:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Or via Python entrypoint (reads from Settings):
```python
# In main.py __main__ block
uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
```

---

## Storage

| Component | Technology | Location | Auto-Created |
|---|---|---|---|
| User data | JSON flat file | `$DATA_DIR/users.json` | Yes (on first write) |
| Task data | JSON flat file | `$DATA_DIR/tasks.json` | Yes (Unit 2, on first write) |
| Data directory | Local filesystem | `$DATA_DIR` (default: `./data/`) | Yes (startup lifespan) |

**Data directory rules**:
- Created at application startup via lifespan event if it does not exist
- Must be writable; readiness check (`/health/ready`) verifies write access
- `.gitignore` must exclude `data/` to prevent committing user data

---

## Networking

| Component | Value | Source |
|---|---|---|
| Host | `APP_HOST` env var | Default: `127.0.0.1` (localhost only) |
| Port | `APP_PORT` env var | Default: `8000` |
| Protocol | HTTP (no TLS) | Local dev only — TLS not required |
| Base URL | `http://localhost:8000` | Derived from host + port |

**API base paths**:
```
http://localhost:8000/auth/register
http://localhost:8000/auth/login
http://localhost:8000/auth/logout
http://localhost:8000/auth/me
http://localhost:8000/health/live
http://localhost:8000/health/ready
```

---

## Configuration (Updated Settings Model)

```python
class Settings(BaseSettings):
    # Auth — required
    JWT_SECRET_KEY: str                  # no default — must be set in .env

    # Auth — optional
    JWT_EXPIRY_MINUTES: int = 60

    # Storage
    DATA_DIR: str = "./data"

    # Server
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    # Observability
    LOG_LEVEL: str = "INFO"             # DEBUG | INFO | WARNING | ERROR

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
```

**Updated `.env.example`**:
```dotenv
# Required — generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=your-secret-key-here

# Optional — defaults shown
JWT_EXPIRY_MINUTES=60
DATA_DIR=./data
APP_HOST=127.0.0.1
APP_PORT=8000
LOG_LEVEL=INFO
```

---

## Logging

| Aspect | Decision | Detail |
|---|---|---|
| Output | stdout only | JSON lines to terminal |
| Format | python-json-logger | One JSON object per line |
| Log file | None | Redirect via shell if needed: `uvicorn ... 2>&1 \| tee app.log` |
| Log level | Configurable | `LOG_LEVEL` env var (default: INFO) |
| Rotation | N/A | stdout only; no rotation needed |

---

## Monitoring

| Aspect | Decision |
|---|---|
| Cloud monitoring | N/A — local dev |
| Alerting | N/A — local dev |
| Distributed tracing | N/A — single process |
| Metrics | N/A — local dev |
| Health checks | `/health/live` + `/health/ready` (process-level only) |

---

## Security Boundaries (Local Dev)

| Concern | Local Dev Decision | Production Note |
|---|---|---|
| TLS/HTTPS | Not configured | Required before production |
| CORS | `allow_origins=["*"]` | Must be restricted to known origins |
| JWT_SECRET_KEY | In `.env` (local file) | Must use secrets manager (AWS SSM, Vault, etc.) |
| Data directory | Local filesystem, no encryption | Must use encrypted storage |
| Network | Localhost only (`127.0.0.1`) | Needs proper networking config |

---

## `.gitignore` Additions Required

```gitignore
# Environment
.env
.env.*
!.env.example

# Data files (never commit user data)
data/

# Logs
logs/
*.log

# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.coverage
htmlcov/
dist/
*.egg-info/
```

---

## Extension Compliance Summary

| Rule | Status | Notes |
|---|---|---|
| SECURITY-09 (Hardening) | Compliant | JWT_SECRET_KEY via env var, .env excluded from git |
| SECURITY-06 (IAM) | N/A | No cloud IAM — local dev |
| SECURITY-07 (Network) | N/A | No cloud network config — local dev |
| SECURITY-01 (Encryption at rest) | N/A | Local filesystem — no cloud storage |
| RESILIENCY-04 (Health checks) | Compliant | /health/live + /health/ready |
| RESILIENCY-02 (Backup) | N/A | Local dev — no cloud backup |

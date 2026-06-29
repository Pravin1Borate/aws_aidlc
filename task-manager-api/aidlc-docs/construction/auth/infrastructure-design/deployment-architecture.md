# Deployment Architecture — Unit 1: Authentication

## Runtime Directory Structure

```
task-manager-api/               ← project root (git repo root)
├── src/                        ← application source (all Python packages)
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── schemas.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py
│   │   ├── errors.py
│   │   ├── logging.py
│   │   ├── middleware.py
│   │   ├── health.py
│   │   └── storage.py          ← Unit 1 scaffolds this; Unit 2 fully implements
│   ├── config.py
│   ├── dependencies.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   └── auth/
│   ├── integration/
│   │   └── auth/
│   └── pbt/
│       └── auth/
├── data/                       ← runtime data (gitignored)
│   ├── users.json              ← created on first user registration
│   └── tasks.json              ← created by Unit 2 on first task creation
├── .env                        ← local secrets (gitignored)
├── .env.example                ← committed template (no secrets)
├── .gitignore
├── pyproject.toml              ← pytest, coverage, hypothesis config
├── requirements.txt            ← pinned runtime deps
└── requirements-dev.txt        ← pinned dev/test deps
```

---

## Developer Setup Steps

### 1. Create virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env — set JWT_SECRET_KEY to a random 32-byte hex string:
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Run the server
```bash
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

Or using the Python entrypoint:
```bash
python -m src.main
```

### 5. Verify startup
```bash
curl http://localhost:8000/health/live
# → {"status": "ok", "service": "task-manager-api"}

curl http://localhost:8000/health/ready
# → {"status": "ready", "checks": {"jwt_config": true, "data_dir": true}}
```

---

## Process Architecture

```
Developer Machine
┌─────────────────────────────────────────────────────┐
│                                                     │
│   Terminal / IDE                                    │
│   ┌─────────────────────────────────────────────┐  │
│   │  uvicorn process (single worker)            │  │
│   │  ┌────────────────────────────────────────┐ │  │
│   │  │  FastAPI app                           │ │  │
│   │  │  ├── CORSMiddleware                   │ │  │
│   │  │  ├── CorrelationIdMiddleware           │ │  │
│   │  │  ├── slowapi RateLimiter               │ │  │
│   │  │  ├── auth_router (/auth/*)             │ │  │
│   │  │  └── health_router (/health/*)         │ │  │
│   │  │                                        │ │  │
│   │  │  In-memory state:                      │ │  │
│   │  │  └── token_blacklist: set[str]         │ │  │
│   │  └────────────────────────────────────────┘ │  │
│   │         ↕ JSON reads/writes                 │  │
│   │  ┌────────────────────────────────────────┐ │  │
│   │  │  ./data/users.json                     │ │  │
│   │  └────────────────────────────────────────┘ │  │
│   └─────────────────────────────────────────────┘  │
│                                                     │
│   Logs → stdout (terminal)                         │
│                                                     │
└─────────────────────────────────────────────────────┘
         ↑ HTTP requests
   curl / Postman / Browser
   (localhost:8000)
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `JWT_SECRET_KEY` | Yes | — | HS256 signing key — min 32 chars recommended |
| `JWT_EXPIRY_MINUTES` | No | `60` | Token lifetime in minutes |
| `DATA_DIR` | No | `./data` | Path to JSON data directory |
| `APP_HOST` | No | `127.0.0.1` | Bind address for uvicorn |
| `APP_PORT` | No | `8000` | Listen port for uvicorn |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity: DEBUG, INFO, WARNING, ERROR |

---

## Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Property-based tests only
pytest -m pbt

# Integration tests only
pytest -m integration

# With coverage report
pytest --cov=src --cov-report=term-missing

# Hypothesis with CI profile (max_examples=200)
HYPOTHESIS_PROFILE=ci pytest -m pbt
```

---

## Common Startup Failures and Fixes

| Error | Cause | Fix |
|---|---|---|
| `RuntimeError: JWT_SECRET_KEY must be set` | `.env` missing or JWT_SECRET_KEY empty | Copy `.env.example` to `.env` and set the key |
| `Permission denied: ./data` | Data directory not writable | `chmod 755 ./data` or change `DATA_DIR` in `.env` |
| `Address already in use :8000` | Another process on port 8000 | Change `APP_PORT` in `.env` or kill the other process |
| `ModuleNotFoundError: No module named 'src'` | Wrong working directory | Run from project root where `src/` is visible |

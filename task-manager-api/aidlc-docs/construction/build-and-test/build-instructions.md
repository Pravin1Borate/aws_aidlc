# Build Instructions — Task Manager API

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | `python --version` to verify |
| pip | latest | included with Python |
| Git | any | for cloning |

**Required environment variable (MUST set before running):**
```
JWT_SECRET_KEY   — any non-empty string (e.g., openssl rand -hex 32)
```

---

## Step 1: Clone / Enter Project

```bash
cd task-manager-api
```

---

## Step 2: Create and Activate Virtual Environment

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

---

## Step 3: Install Runtime Dependencies

```bash
pip install -r requirements.txt
```

**Expected output**: All packages install without errors.

**Runtime packages installed:**
- `fastapi==0.111.1` — REST framework
- `uvicorn[standard]==0.30.1` — ASGI server
- `pydantic==2.7.4` — data validation
- `pydantic-settings==2.3.4` — settings from .env
- `email-validator==2.1.1` — email validation
- `bcrypt==4.1.3` — password hashing
- `python-jose[cryptography]==3.3.0` — JWT
- `slowapi==0.1.9` — rate limiting
- `python-json-logger==2.0.7` — structured logging

---

## Step 4: Install Dev Dependencies

```bash
pip install -r requirements-dev.txt
```

**Dev packages installed:**
- `pytest==8.2.2` + `pytest-cov==5.0.0`
- `hypothesis==6.104.2` — property-based testing
- `httpx==0.27.0` — async HTTP client (TestClient)
- `anyio[trio]==4.4.0` — async test support
- `mypy==1.10.0` — type checking

---

## Step 5: Configure Environment

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and set the required value:
```dotenv
JWT_SECRET_KEY=<your-secret-key-here>   # Required — use: python -c "import secrets; print(secrets.token_hex(32))"
JWT_EXPIRY_MINUTES=60
DATA_DIR=./data
APP_HOST=127.0.0.1
APP_PORT=8000
LOG_LEVEL=INFO
```

> **IMPORTANT**: Never commit `.env` — it is in `.gitignore`.

---

## Step 6: Verify Build (Static Type Check)

```bash
python -m mypy src/ --ignore-missing-imports
```

**Expected output**: No errors reported.

---

## Step 7: Start the Server (Optional — for manual testing)

```bash
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

**Expected startup output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process ...
INFO:     Started server process ...
```

**Interactive API docs**: http://127.0.0.1:8000/docs  
**Health check**: http://127.0.0.1:8000/health/live

---

## Build Artifacts

| Artifact | Location | Description |
|---|---|---|
| Source packages | `src/` | Application code |
| Runtime data | `data/` | Created at first use (gitignored) |
| Test cache | `.pytest_cache/` | pytest cache (gitignored) |
| Coverage | `.coverage` | Coverage data file |

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'src'`
Run from the **project root** (the directory containing `src/` and `pyproject.toml`):
```bash
cd task-manager-api
python -m pytest ...   # use -m to run as module, not pytest directly
```

### `RuntimeError: JWT_SECRET_KEY must be set`
The `.env` file is missing or `JWT_SECRET_KEY` is empty. Set it in `.env`.

### `bcrypt` version warning
Acceptable — bcrypt 4.x changed the API slightly; the code is compatible.

### Port 8000 already in use
```bash
# Use a different port
python -m uvicorn src.main:app --port 8001
```

# Unit Test Execution — Task Manager API

## Overview

Unit tests are isolated (no real HTTP, no real file I/O for service tests). Each test function gets a fresh in-memory state via pytest fixtures.

**Test framework**: pytest 8.2.2  
**Coverage tool**: pytest-cov  
**Minimum coverage**: 80% (enforced via `pyproject.toml`)

---

## Prerequisites

```bash
# Virtual environment active, dev dependencies installed
pip install -r requirements-dev.txt

# JWT_SECRET_KEY set in .env (required for TestClient tests)
```

---

## Run All Unit Tests

```bash
python -m pytest tests/unit/ -v
```

**Expected**: All tests pass, 0 failures.

---

## Run Unit Tests by Module

```bash
# Auth unit tests (Unit 1)
python -m pytest tests/unit/auth/ -v

# Task repository tests (Unit 2)
python -m pytest tests/unit/tasks/test_task_repository.py -v

# Task service tests (Unit 2)
python -m pytest tests/unit/tasks/test_task_service.py -v

# User service tests (Unit 2)
python -m pytest tests/unit/users/test_user_service.py -v
```

---

## Run with Coverage Report

```bash
# HTML report
python -m pytest tests/unit/ --cov=src --cov-report=html --cov-report=term-missing

# Open coverage report
start htmlcov/index.html      # Windows
open htmlcov/index.html       # macOS
```

**Expected coverage**: ≥ 80% overall (enforced — pytest fails below this threshold).

---

## Unit Test Inventory

### Unit 1: Authentication

| File | Tests | What is Covered |
|---|---|---|
| `tests/unit/auth/test_security_utils.py` | 12 | password hashing, JWT lifecycle, blacklist |
| `tests/unit/auth/test_auth_service.py` | 13 | register, login (lockout), logout, get_current_user |
| `tests/unit/auth/test_user_repository.py` | 7 | CRUD, case-insensitive email lookup |
| `tests/unit/test_health.py` | 5 | liveness + readiness probes |

### Unit 2: Task Management

| File | Tests | What is Covered |
|---|---|---|
| `tests/unit/tasks/test_task_repository.py` | 12 | find_by_id, find_filtered (all filter combos), pagination, sort order, save |
| `tests/unit/tasks/test_task_service.py` | 20 | create (assignee resolution), get_by_id, list, full_update, partial_update (tag merge), delete (access control) |
| `tests/unit/users/test_user_service.py` | 5 | list_users, get_by_id |

**Total unit tests**: ~74

---

## Key Test Fixtures (`tests/conftest.py`)

| Fixture | Scope | Purpose |
|---|---|---|
| `clear_token_blacklist` | autouse, function | Clears in-memory blacklist before/after each test |
| `tmp_data_dir` | function | Temp dir for JSON files — isolated per test |
| `patch_settings` | function | Patches `DATA_DIR` + `JWT_SECRET_KEY` in settings |
| `client` | function | FastAPI `TestClient` with patched settings |

---

## Run Property-Based Tests (Hypothesis)

```bash
# All PBT tests
python -m pytest tests/pbt/ -v

# With verbose Hypothesis output
python -m pytest tests/pbt/ -v --hypothesis-show-statistics
```

**Hypothesis profiles** (configured in `pyproject.toml`):
- `ci`: 200 examples per property (default)
- `dev`: 50 examples per property (faster local runs)

```bash
# Use the faster dev profile
python -m pytest tests/pbt/ -v -p hypothesis --hypothesis-profile=dev
```

### PBT Inventory

| File | Properties | What is Tested |
|---|---|---|
| `tests/pbt/auth/test_security_properties.py` | 6 | password round-trip, JWT round-trip/tamper, blacklist idempotency, lockout invariant, email normalization |
| `tests/pbt/tasks/test_task_properties.py` | 7 | tag merge (no duplicates, remove semantics, idempotency, add presence), response never exposes deleted_at, owner_id preserved, due_date filter correctness |

---

## Fix Failing Tests

1. Read the failure output — pytest prints the exact assertion that failed
2. Look at the fixture chain — most failures are data setup issues
3. If it's a `conftest.py` issue, check that `patch_settings` is in the fixture chain
4. Run a single failing test in isolation:
   ```bash
   python -m pytest tests/unit/tasks/test_task_service.py::TestCreate::test_creates_task_with_defaults -v -s
   ```

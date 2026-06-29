# Code Summary — Unit 1: Authentication

## Files Created

### Project Root
| File | Purpose |
|---|---|
| `requirements.txt` | Pinned runtime dependencies (9 packages) |
| `requirements-dev.txt` | Pinned dev/test dependencies (6 packages) |
| `pyproject.toml` | pytest, coverage, Hypothesis configuration |
| `.env.example` | Environment variable template (no secrets) |
| `.gitignore` | Excludes .env, data/, logs/, __pycache__ |

### Application Source (`src/`)
| File | Purpose | Stories |
|---|---|---|
| `src/config.py` | Settings (pydantic-settings, 6 env vars) | All |
| `src/dependencies.py` | FastAPI DI: oauth2_scheme, get_auth_service, get_current_user | US-03 |
| `src/main.py` | App factory, middleware stack, exception handlers, routers | All |
| `src/auth/schemas.py` | Pydantic models: UserCreate, LoginRequest, UserResponse, TokenResponse, User | All |
| `src/auth/repository.py` | UserRepository — find_by_email, find_by_id, save | US-01, US-02 |
| `src/auth/service.py` | AuthService — register, login, logout, get_current_user | US-01–04 |
| `src/auth/router.py` | AuthRouter — /register, /login, /logout, /me (slowapi rate limits) | US-01–04 |
| `src/core/security.py` | SecurityUtils — bcrypt, JWT, token blacklist | US-01–04 |
| `src/core/errors.py` | AppException hierarchy (401, 403, 404, 409) | All |
| `src/core/logging.py` | StructuredLogger — python-json-logger, JSON lines to stdout | All |
| `src/core/middleware.py` | CorrelationIdMiddleware — UUID4 per request, X-Correlation-ID header | All |
| `src/core/health.py` | HealthRouter — /health/live + /health/ready | — |
| `src/core/storage.py` | JsonFileStorage — atomic write, CRUD operations | US-01, US-02 |
| `src/core/rate_limiter.py` | slowapi Limiter singleton | US-01–04 |

### Tests (`tests/`)
| File | Type | Test Count | Coverage |
|---|---|---|---|
| `tests/conftest.py` | Fixtures | — | Shared: client, patch_settings, tmp_data_dir, clear_blacklist |
| `tests/unit/auth/test_security_utils.py` | Unit | 12 | bcrypt hash/verify, JWT create/decode/expire/tamper, blacklist |
| `tests/unit/auth/test_auth_service.py` | Unit | 13 | register, login (lockout, counter), logout, get_current_user |
| `tests/unit/auth/test_user_repository.py` | Unit | 7 | CRUD, case-insensitive lookup |
| `tests/unit/test_health.py` | Unit | 5 | /health/live, /health/ready, degraded state |
| `tests/integration/auth/test_auth_endpoints.py` | Integration | 16 | All 4 endpoints + health, end-to-end flows |
| `tests/pbt/auth/test_security_properties.py` | PBT | 6 | 6 Hypothesis properties (round-trip, idempotence, invariants) |

**Total tests: 59**

## Story Traceability

| Story | Files Implementing | Test Files |
|---|---|---|
| US-01: Register | service.py, repository.py, router.py, schemas.py | test_auth_service.py, test_auth_endpoints.py |
| US-02: Login + JWT | service.py, security.py, router.py | test_auth_service.py, test_auth_endpoints.py |
| US-03: Protected access | dependencies.py, service.py, router.py | test_auth_service.py, test_auth_endpoints.py |
| US-04: Logout + blacklist | service.py, security.py, router.py | test_auth_service.py, test_auth_endpoints.py |

## Known Limitations

| Limitation | Location | Production Resolution |
|---|---|---|
| Token blacklist cleared on restart | `core/security.py` `_blacklist` set | Replace with Redis or DB table |
| bcrypt blocks event loop (~300–400ms) | `auth/service.py` — synchronous bcrypt calls | Wrap in `asyncio.run_in_executor` |
| CORS allows all origins | `main.py` CORSMiddleware | Restrict `allow_origins` to known domains |
| JSON flat file, no transactions | `core/storage.py` | Replace with a proper database |
| SECURITY-12: No breached password check | `auth/service.py register()` | Integrate HIBP k-anonymity API |

# Code Generation Plan — Unit 1: Authentication

## Unit Context

- **Unit**: Unit 1 — Authentication
- **Stories**: US-01, US-02, US-03, US-04
- **Dependencies**: None (Unit 1 is the foundation)
- **Interfaces locked for Unit 2**: `get_current_user`, `UserRepository`, `AppException`, `StructuredLogger`, `Settings`
- **Project type**: Greenfield monolith — `src/` layout
- **Workspace root**: `C:\Users\pravin.borate\Documents\Tech-Talk\aws_aidlc\task-manager-api`

## Story Coverage

| Story | Description | Steps |
|---|---|---|
| US-01 | Register with email and password | 10, 11, 12, 13, 17, 18, 19, 21, 22 |
| US-02 | Login and receive JWT | 10, 12, 13, 14, 18, 21, 22 |
| US-03 | Access protected resources with token | 13, 15, 16, 18, 21 |
| US-04 | Logout and invalidate token | 12, 13, 14, 18, 21 |

---

## Generation Steps

### SECTION A: Project Structure Setup

- [x] **Step 1**: Create project root config files
  - `requirements.txt` — pinned runtime dependencies
  - `requirements-dev.txt` — pinned dev/test dependencies
  - `.env.example` — template with all env vars, no secrets
  - `.gitignore` — excludes .env, data/, logs/, __pycache__, .pytest_cache, .coverage

- [x] **Step 2**: Create `pyproject.toml`
  - `[tool.pytest.ini_options]` — testpaths, markers (unit/integration/pbt), addopts
  - `[tool.coverage.run]` and `[tool.coverage.report]` — source=src, fail_under=80
  - `[tool.hypothesis]` — suppress_health_check, CI profile (200 examples), dev profile (50)

- [x] **Step 3**: Create Python package `__init__.py` files and `tests/conftest.py`
  - `src/__init__.py`
  - `src/auth/__init__.py`
  - `src/core/__init__.py`
  - `tests/__init__.py`
  - `tests/unit/__init__.py`
  - `tests/unit/auth/__init__.py`
  - `tests/integration/__init__.py`
  - `tests/integration/auth/__init__.py`
  - `tests/pbt/__init__.py`
  - `tests/pbt/auth/__init__.py`
  - `tests/conftest.py` — shared fixtures: `tmp_data_dir`, `app_settings`, `test_client`

---

### SECTION B: Core Infrastructure (Unit 1 owns)

- [x] **Step 4**: Generate `src/config.py`
  - `Settings(BaseSettings)` with all 6 env vars
  - Module-level `settings = Settings()` singleton
  - pydantic-settings with `.env` file support

- [x] **Step 5**: Generate `src/core/errors.py`
  - `AppException(Exception)` base with `status_code` + `message`
  - `UnauthorizedError` (401), `ConflictError` (409), `NotFoundError` (404), `ForbiddenError` (403)

- [x] **Step 6**: Generate `src/core/logging.py`
  - `configure_logging(level: str)` — stdlib logging + JsonFormatter (python-json-logger)
  - JSON lines to stdout
  - `get_logger(name: str)` helper

- [x] **Step 7**: Generate `src/core/middleware.py`
  - `CorrelationIdMiddleware(BaseHTTPMiddleware)`
  - UUID4 per request → `request.state.correlation_id`
  - JSON log line at request start and completion (method, path, status, duration_ms)
  - `X-Correlation-ID` response header

- [x] **Step 8**: Generate `src/core/health.py`
  - `health_router = APIRouter(prefix="/health", tags=["health"])`
  - `GET /health/live` → `{"status": "ok", "service": "task-manager-api"}`
  - `GET /health/ready` → jwt_config + data_dir checks, `{"status": "ready"|"degraded", "checks": {...}}`

- [x] **Step 9**: Generate `src/core/storage.py`
  - `JsonFileStorage` class — `read_all`, `write_all`, `find_by_id`, `upsert`, `delete_by_id`
  - Atomic write pattern (write-to-temp → `os.replace()`)
  - Thread-safe for single-process use

---

### SECTION C: Auth Business Logic Layer

- [x] **Step 10**: Generate `src/auth/schemas.py`
  - `UserCreate` — email (EmailStr), password (min_length=8), full_name (optional)
  - `LoginRequest` — email (EmailStr), password (str)
  - `UserResponse` — id, email, full_name, created_at (no password_hash)
  - `TokenResponse` — access_token, token_type="bearer", expires_in (seconds)
  - `User` (internal model) — all fields including password_hash, failed_login_attempts, lockout_until
  - `HealthResponse`, `ReadinessResponse` — for health endpoints

- [x] **Step 11**: Generate `src/auth/repository.py`
  - `UserRepository` wrapping `JsonFileStorage`
  - `find_by_email(email: str) -> User | None`
  - `find_by_id(user_id: str) -> User | None`
  - `save(user: User) -> User` — create or update, sets updated_at

- [x] **Step 12**: Generate `src/auth/service.py`
  - `AuthService` with `UserRepository` + `SecurityUtils` injected
  - `register(data: UserCreate) -> UserResponse` — BR-AUTH-01 full flow
  - `login(data: LoginRequest) -> TokenResponse` — BR-AUTH-02 full flow with lockout
  - `logout(token: str) -> None` — BR-AUTH-04 full flow
  - `get_current_user(token: str) -> UserResponse` — BR-AUTH-03 full flow

- [x] **Step 13**: Generate `src/core/security.py`
  - `hash_password(plain: str) -> str` — bcrypt, cost factor 12
  - `verify_password(plain: str, hashed: str) -> bool` — bcrypt constant-time
  - `create_access_token(data: dict, expires_delta: timedelta | None) -> str` — python-jose HS256
  - `decode_access_token(token: str) -> dict` — raises JWTError on invalid/expired
  - `blacklist_token(token: str) -> None` — idempotent, module-level set
  - `is_blacklisted(token: str) -> bool`

---

### SECTION D: Auth API Layer

- [x] **Step 14**: Generate `src/auth/router.py`
  - `auth_router = APIRouter(prefix="/auth", tags=["auth"])`
  - `POST /register` — `@limiter.limit("20/minute")`, calls `auth_service.register`
  - `POST /login` — `@limiter.limit("20/minute")`, calls `auth_service.login`
  - `POST /logout` — `@limiter.limit("100/minute")`, `Depends(get_current_user)`, calls `auth_service.logout`
  - `GET /me` — `@limiter.limit("100/minute")`, returns current user from `get_current_user`

- [x] **Step 15**: Generate `src/dependencies.py`
  - `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")`
  - `get_auth_service() -> AuthService` — dependency factory
  - `get_current_user(token, auth_service) -> UserResponse` — full token validation

- [x] **Step 16**: Generate `src/main.py`
  - `lifespan` context manager — startup validation + data dir creation
  - `app = FastAPI(title="Task Manager API", lifespan=lifespan)`
  - Middleware stack (in order): CORSMiddleware, CorrelationIdMiddleware
  - slowapi: `limiter = Limiter(key_func=get_remote_address)`, `app.state.limiter`, `SlowAPIMiddleware`
  - Global exception handlers: `AppException`, `RateLimitExceeded`, fallback `Exception`
  - Include routers: `auth_router`, `health_router`
  - `if __name__ == "__main__": uvicorn.run(...)` entrypoint

---

### SECTION E: Unit Tests

- [x] **Step 17**: Generate `tests/unit/auth/test_security_utils.py`
  - `test_hash_password_produces_valid_bcrypt_hash`
  - `test_verify_password_correct_plain`
  - `test_verify_password_wrong_plain`
  - `test_create_access_token_contains_expected_claims`
  - `test_decode_valid_token`
  - `test_decode_expired_token_raises`
  - `test_decode_tampered_token_raises`
  - `test_blacklist_token_marks_as_blacklisted`
  - `test_blacklist_idempotent`
  - `test_is_blacklisted_returns_false_for_unknown_token`

- [x] **Step 18**: Generate `tests/unit/auth/test_auth_service.py`
  - `test_register_success` (US-01)
  - `test_register_duplicate_email_raises_conflict` (US-01)
  - `test_register_invalid_email_raises` (US-01)
  - `test_login_success_returns_token` (US-02)
  - `test_login_wrong_password_increments_counter` (US-02)
  - `test_login_fifth_failure_locks_account` (US-02)
  - `test_login_locked_account_raises` (US-02)
  - `test_login_success_resets_counter` (US-02)
  - `test_logout_blacklists_token` (US-04)
  - `test_logout_invalid_token_raises` (US-04)
  - `test_get_current_user_valid_token` (US-03)
  - `test_get_current_user_expired_token_raises` (US-03)
  - `test_get_current_user_blacklisted_token_raises` (US-03)

- [x] **Step 19**: Generate `tests/unit/auth/test_user_repository.py`
  - `test_save_and_find_by_email`
  - `test_save_and_find_by_id`
  - `test_find_by_email_not_found_returns_none`
  - `test_save_updates_existing_user`
  - `test_email_case_insensitive_lookup`

- [x] **Step 20**: Generate `tests/unit/test_health.py`
  - `test_liveness_returns_ok`
  - `test_readiness_returns_ready_when_configured`
  - `test_readiness_returns_degraded_when_data_dir_missing`

---

### SECTION F: Integration Tests

- [x] **Step 21**: Generate `tests/integration/auth/test_auth_endpoints.py`
  - `test_register_endpoint_success` (US-01)
  - `test_register_duplicate_returns_409` (US-01)
  - `test_login_endpoint_success_returns_token` (US-02)
  - `test_login_wrong_password_returns_401` (US-02)
  - `test_me_endpoint_with_valid_token` (US-03)
  - `test_me_endpoint_without_token_returns_401` (US-03)
  - `test_logout_endpoint_success` (US-04)
  - `test_me_after_logout_returns_401` (US-04)
  - `test_health_live`
  - `test_health_ready`

---

### SECTION G: Property-Based Tests

- [x] **Step 22**: Generate `tests/pbt/auth/test_security_properties.py`
  - Property 1: `test_password_hash_roundtrip` — `verify(p, hash(p)) == True` for all valid passwords
  - Property 2: `test_wrong_password_never_verifies` — `verify(w, hash(p)) == False` when `w != p`
  - Property 3: `test_jwt_roundtrip` — decoded payload contains all keys from original dict
  - Property 4: `test_blacklist_idempotent` — state same after 1 or 2 blacklist calls
  - Property 5: `test_failed_login_counter_never_negative` — invariant over sequences of failures
  - Property 6: `test_email_normalization_invariant` — stored email always lowercase

---

### SECTION H: Documentation

- [x] **Step 23**: Generate `aidlc-docs/construction/auth/code/code-summary.md`
  - List all files created with paths
  - Story → file mapping
  - Test coverage notes
  - Known limitations (blacklist not persisted, sync bcrypt)

---

## Total: 23 steps across 8 sections
## Stories covered: US-01, US-02, US-03, US-04 (all Unit 1 stories)

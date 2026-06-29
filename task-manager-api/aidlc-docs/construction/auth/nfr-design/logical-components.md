# Logical Components — Unit 1: Authentication

## Middleware Stack (Request Processing Order)

```
Incoming HTTP Request
        |
        v
[1] CORSMiddleware          — fastapi.middleware.cors
        |
        v
[2] CorrelationIdMiddleware — core/middleware.py (custom)
        |                     Generates UUID4, injects into request.state + log context
        v
[3] slowapi RateLimiter     — SlowAPI (app.state.limiter)
        |                     Applied per-endpoint via @limiter.limit() decorators
        v
[4] FastAPI Router Dispatch
        |
        +---> /auth/*   → auth_router
        +---> /health/* → health_router
        +---> /         → (Unit 2 adds tasks_router, users_router)
        |
        v
[5] get_current_user        — FastAPI dependency (dependencies.py)
        |                     Injected on protected routes only
        v
[6] Route Handler           — Business logic via AuthService
        |
        v
[7] Response + X-Correlation-ID header
```

---

## Component: CorrelationIdMiddleware

**File**: `core/middleware.py`
**Type**: Starlette `BaseHTTPMiddleware`

**Responsibilities**:
- Generate UUID4 correlation ID for every request
- Store in `request.state.correlation_id`
- Bind to logger context for all downstream log calls
- Add `X-Correlation-ID` header to response
- Log request start and completion (method, path, status, duration_ms)

**Interface**:
```python
class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response
```

---

## Component: AuthRouter

**File**: `auth/router.py`
**Prefix**: `/auth`
**Tag**: `auth`

| Method | Path | Rate Limit | Auth Required | Handler |
|---|---|---|---|---|
| POST | `/register` | 20/min (IP) | No | `register` |
| POST | `/login` | 20/min (IP) | No | `login` |
| POST | `/logout` | 100/min (user) | Yes | `logout` |
| GET | `/me` | 100/min (user) | Yes | `get_me` |

**Dependencies injected**:
- `AuthService` — via `Depends(get_auth_service)`
- `UserResponse` (current user) — via `Depends(get_current_user)` on protected routes
- `Request` — required by slowapi for rate limiting

---

## Component: HealthRouter

**File**: `core/health.py`
**Prefix**: `/health`
**Tag**: `health`

| Method | Path | Rate Limit | Auth Required | Handler |
|---|---|---|---|---|
| GET | `/live` | None | No | `liveness` |
| GET | `/ready` | None | No | `readiness` |

**Readiness checks**:
```python
checks = {
    "jwt_config": bool(settings.JWT_SECRET_KEY),
    "data_dir": Path(settings.DATA_DIR).exists() and os.access(settings.DATA_DIR, os.W_OK)
}
status = "ready" if all(checks.values()) else "degraded"
```

---

## Component: AuthService

**File**: `auth/service.py`

**Dependencies**:
- `UserRepository`
- `SecurityUtils`

**Methods** (from component-methods.md, with pattern annotations):
```python
async def register(self, data: UserCreate) -> UserResponse
    # Pattern: normalize email → uniqueness check → bcrypt hash → persist → return response

async def login(self, data: LoginRequest) -> TokenResponse
    # Pattern: normalize → lockout check → user lookup → bcrypt verify →
    #          increment/reset counter → issue JWT

async def logout(self, token: str) -> None
    # Pattern: full token validation → add to blacklist

async def get_current_user(self, token: str) -> UserResponse
    # Pattern: decode JWT → blacklist check → user lookup → return response
```

---

## Component: SecurityUtils

**File**: `core/security.py`

**Responsibilities**:
- bcrypt password hashing and verification (synchronous, cost factor 12)
- JWT token creation and decoding (python-jose, HS256)
- In-memory token blacklist management (module-level `set[str]`)

**Interface**:
```python
# Password
def hash_password(plain: str) -> str
def verify_password(plain: str, hashed: str) -> bool

# JWT
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str
def decode_access_token(token: str) -> dict  # raises JWTError on invalid/expired

# Blacklist
def blacklist_token(token: str) -> None      # idempotent
def is_blacklisted(token: str) -> bool
```

**Blacklist storage**: Module-level `_blacklist: set[str] = set()`. Process-lifetime only.

---

## Component: UserRepository

**File**: `auth/repository.py`

**Dependencies**: `JsonFileStorage` (from `core/storage.py`, provided by Unit 1 since it's in core/)

**Interface**:
```python
def find_by_email(self, email: str) -> User | None
def find_by_id(self, user_id: str) -> User | None
def save(self, user: User) -> User           # create or update
```

---

## Component: get_current_user (Dependency)

**File**: `dependencies.py`

**Pattern**: FastAPI `Depends()` — runs before the route handler on every protected route.

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    return await auth_service.get_current_user(token)
```

**oauth2_scheme**: `OAuth2PasswordBearer(tokenUrl="/auth/login")` — extracts Bearer token from Authorization header.

---

## Component: Settings

**File**: `config.py`

```python
class Settings(BaseSettings):
    JWT_SECRET_KEY: str                  # required — no default
    JWT_EXPIRY_MINUTES: int = 60
    DATA_DIR: str = "./data"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
```

Instantiated once as a module-level singleton `settings = Settings()`.

---

## Component: StructuredLogger

**File**: `core/logging.py`

**Library**: stdlib `logging` + `python-json-logger` (`pythonjsonlogger.jsonlogger.JsonFormatter`)

**Configuration**:
```python
handler = logging.StreamHandler()
formatter = JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)
handler.setFormatter(formatter)
logging.root.addHandler(handler)
logging.root.setLevel(settings.LOG_LEVEL)
```

**Usage pattern in middleware/services**:
```python
logger = logging.getLogger(__name__)
logger.info("login_attempt", extra={"correlation_id": cid, "email": email})
```

---

## Component: AppException Hierarchy

**File**: `core/errors.py`

```
AppException(Exception)
    status_code: int
    message: str
├── UnauthorizedError(AppException)   status_code=401
├── ConflictError(AppException)       status_code=409
├── NotFoundError(AppException)       status_code=404
└── ForbiddenError(AppException)      status_code=403
```

Global handler in `main.py`:
```python
@app.exception_handler(AppException)
async def handle_app_exception(request, exc: AppException):
    logger.warning(exc.message, extra={"status_code": exc.status_code, ...})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

@app.exception_handler(Exception)
async def handle_unhandled(request, exc: Exception):
    logger.error("Unhandled exception", exc_info=True, ...)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

---

## Application Startup Sequence

**File**: `main.py`

```
1. Load Settings (pydantic-settings reads .env)
   → RuntimeError if JWT_SECRET_KEY missing
2. Configure StructuredLogger
3. Create FastAPI app with lifespan
4. lifespan startup:
   a. Validate JWT_SECRET_KEY non-empty
   b. Create DATA_DIR if not exists
   c. Log "startup complete"
5. Add middleware (order matters — outermost first):
   a. CORSMiddleware
   b. CorrelationIdMiddleware
6. Add slowapi exception handler (SlowAPIMiddleware)
7. Include routers:
   a. auth_router  (prefix=/auth)
   b. health_router (prefix=/health)
```

---

## Data Flow: Login Request (End-to-End)

```
POST /auth/login { email, password }
  → CORSMiddleware (passthrough — same origin in local dev)
  → CorrelationIdMiddleware: generate correlation_id=abc123, log "request start"
  → slowapi: check IP rate limit (20/min) → allow/429
  → auth_router.login(request, data=LoginRequest)
      → AuthService.login(data)
          → normalize email
          → UserRepository.find_by_email(email)
          → check lockout_until
          → SecurityUtils.verify_password(data.password, user.password_hash)
          → on failure: increment counter, UserRepository.save(user), raise UnauthorizedError
          → on success: reset counter, SecurityUtils.create_access_token(...)
          → return TokenResponse
  → CorrelationIdMiddleware: log "request complete" (status=200, duration=312ms)
  → Response + X-Correlation-ID: abc123
```

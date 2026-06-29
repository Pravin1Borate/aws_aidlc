# NFR Design Patterns — Unit 1: Authentication

## Pattern 1: JWT Dependency Injection (Security)

**Satisfies**: SEC-AUTH-02 (access control), BR-AUTH-03 (token validation on every request)

**Pattern**: FastAPI's dependency injection system injects `get_current_user` into every protected route. The dependency validates the token fully (signature → expiry → blacklist → user exists) and returns a `UserResponse`. Routes never touch raw tokens.

```
Request → Router → get_current_user(token) → [validate] → UserResponse → Handler
                                           ↓ (any failure)
                                        401 Unauthorized
```

**Key constraint**: `get_current_user` is synchronous-safe — JWT decode and set lookup are both < 1ms. No executor needed.

---

## Pattern 2: Synchronous bcrypt (Performance — Q1=B)

**Satisfies**: SEC-AUTH-01, PERF-AUTH-01/02

**Pattern**: bcrypt `hashpw` and `checkpw` called synchronously from `SecurityUtils`. No thread pool executor. The event loop blocks for ~200–400ms per call.

**Accepted tradeoff**: Local dev single-user testing — no concurrent requests expected. PERF-AUTH-01/02 targets (< 800ms P95) remain achievable. Must be revisited before production deployment.

```
SecurityUtils.hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()

SecurityUtils.verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
```

---

## Pattern 3: Per-Router Rate Limiting (Security — Q2=B)

**Satisfies**: SEC-AUTH-01 (20/min unauthenticated), SEC-AUTH-02 (100/min authenticated), SECURITY-11

**Pattern**: slowapi limiter attached to app state. Each endpoint explicitly decorated. Health endpoints carry no decorator — excluded from limiting.

```
# Unauthenticated endpoints (IP-based, 20/min)
@router.post("/register")
@limiter.limit("20/minute")
async def register(request: Request, ...): ...

@router.post("/login")
@limiter.limit("20/minute")
async def login(request: Request, ...): ...

# Authenticated endpoints (user-based, 100/min)
@router.post("/logout")
@limiter.limit("100/minute")
async def logout(request: Request, ...): ...

@router.get("/me")
@limiter.limit("100/minute")
async def me(request: Request, ...): ...

# Health endpoints — NO decorator (exempt from rate limiting)
@router.get("/health/live")
async def liveness(): ...
```

**Key constraint**: slowapi requires `request: Request` as the first parameter on every rate-limited endpoint.

---

## Pattern 4: FastAPI Default Error Responses (Q3=A)

**Satisfies**: SEC-AUTH-07 (generic error responses), REL-AUTH-01

**Pattern**: No custom error envelope. FastAPI's built-in `HTTPException` raises `{"detail": "message"}`. Pydantic validation failures produce `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}`.

Custom `AppException` hierarchy maps to `HTTPException` in the global handler:

```
AppException (base)
├── UnauthorizedError  → 401, {"detail": "message"}
├── ConflictError      → 409, {"detail": "message"}
├── NotFoundError      → 404, {"detail": "message"}
└── ValidationError    → 422, {"detail": "message"}

# Global handler in main.py:
@app.exception_handler(AppException)
async def app_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
```

Internal exceptions (non-AppException): caught by fallback handler, logged with full traceback, returned as `{"detail": "Internal server error"}` (500).

---

## Pattern 5: Request Correlation ID Middleware (Observability — Q5=A)

**Satisfies**: MAINT-AUTH-03, SEC-AUTH-08 (structured logging)

**Pattern**: ASGI middleware generates a UUID4 correlation ID for every request, regardless of incoming headers. Stored in `request.state.correlation_id`. Passed to all log entries within that request. Returned as `X-Correlation-ID` response header.

```
Request → CorrelationIdMiddleware → generates UUID4 → request.state.correlation_id
                                 → injects into log context
                                 → adds X-Correlation-ID to response
```

Log entry structure per request:
```json
{"timestamp": "...", "level": "INFO", "correlation_id": "uuid4", "method": "POST",
 "path": "/auth/login", "status_code": 200, "duration_ms": 312, "user_id": "uuid4|null"}
```

---

## Pattern 6: Permissive CORS for Local Dev (Q4=A)

**Satisfies**: Local dev accessibility for browser clients

**Pattern**: `CORSMiddleware` added to app with permissive settings. Code comment marks this as dev-only configuration.

```python
# NOTE: Permissive CORS for local development only.
# Tighten allow_origins before any production deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Pattern 7: Liveness + Readiness Health Checks (Availability)

**Satisfies**: AVAIL-AUTH-01/02, RESILIENCY-04

**Pattern**: Two separate endpoints in `health_router`. Liveness checks nothing (process-alive). Readiness validates configuration and data directory.

```
GET /health/live  → {"status": "ok", "service": "task-manager-api"}
GET /health/ready → {"status": "ready"|"degraded",
                     "checks": {"jwt_config": true|false, "data_dir": true|false}}
```

Readiness checks:
1. `jwt_config`: `settings.JWT_SECRET_KEY` is non-empty
2. `data_dir`: `Path(settings.DATA_DIR).exists()` and `os.access(..., os.W_OK)`

Both endpoints: no authentication, no rate limiting, not included in request access logs.

---

## Pattern 8: Atomic JSON Write (Reliability)

**Satisfies**: REL-AUTH-02

**Pattern**: Write to a `.tmp` file first, then `os.replace()` (atomic rename on POSIX, near-atomic on Windows). Prevents partial writes from corrupting the data file.

```
write_all(records):
    tmp = Path(self._path).with_suffix('.tmp')
    tmp.write_text(json.dumps(records, ...))
    os.replace(tmp, self._path)
```

---

## Pattern 9: Fail-Fast Startup Validation (Reliability)

**Satisfies**: AVAIL-AUTH-04, REL-AUTH-03

**Pattern**: Application lifespan event validates critical config before accepting requests. Exits with clear error message if validation fails.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation
    if not settings.JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY must be set in environment")
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
    logger.info("Startup validation passed")
    yield
    # Shutdown (no cleanup needed for in-memory state)
```

---

## Extension Compliance Summary

| Extension Rule | Pattern Applied | Status |
|---|---|---|
| SECURITY-11 (Rate limiting) | Pattern 3 — per-router slowapi decorators | Compliant |
| SECURITY-12 (Auth) | Pattern 2 — synchronous bcrypt cost-12 | Compliant (breach check gap remains) |
| SECURITY-08 (Access control) | Pattern 1 — JWT dependency injection | Compliant |
| SECURITY-09 (Hardening) | Pattern 4 — generic error responses | Compliant |
| SECURITY-03 (Logging) | Pattern 5 — correlation ID + JSON lines | Compliant |
| RESILIENCY-04 (Health checks) | Pattern 7 — live + ready endpoints | Compliant |
| PBT-01 (Properties identified) | Defined in business-logic-model.md | Compliant |

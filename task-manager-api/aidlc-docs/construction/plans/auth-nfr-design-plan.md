# NFR Design Plan — Unit 1: Authentication

## Plan Execution Checklist

- [x] Analyze NFR requirements artifacts
- [x] Ask clarifying questions on design patterns
- [x] Generate `nfr-design-patterns.md`
- [x] Generate `logical-components.md`

---

## Context Already Decided (No Questions Needed)

From nfr-requirements.md and tech-stack-decisions.md:
- Atomic write pattern for JSON files — locked
- Global exception handler — locked
- JWT validation as FastAPI dependency (get_current_user) — locked
- slowapi rate limiter — locked
- Startup fail-fast for missing JWT_SECRET_KEY — locked

---

## Questions Requiring User Input

### Q1: Async bcrypt — thread pool execution

bcrypt's `checkpw` and `hashpw` are CPU-bound and blocking. In an async FastAPI app,
running them directly on the event loop blocks all concurrent requests for ~300–400ms
per call. Running them in a thread pool executor prevents this.

A) **Use executor** — `await asyncio.get_event_loop().run_in_executor(None, bcrypt.checkpw, ...)`.
   Non-blocking, correct async behavior. Slight added complexity in SecurityUtils.

B) **Run synchronously** — call bcrypt directly without executor. Simpler code; blocks the
   event loop for ~300–400ms per login/register. Acceptable for local dev single-user testing.

[Answer]: B

---

### Q2: Rate limiter scope

slowapi can be applied at different granularities. Which approach?

A) **Global middleware** — attach limiter to the FastAPI app instance. All routes inherit
   the default limit. Per-route overrides via `@limiter.limit(...)` decorator. Simpler to
   reason about; one place to configure.

B) **Per-router decorators only** — no global default; each endpoint explicitly decorated.
   More verbose but no accidental coverage gaps or unexpected rate-limiting of internal routes.

[Answer]: B

---

### Q3: API error response envelope

When validation fails or auth errors occur, what should the response body look like?

A) **FastAPI default** — `{"detail": "error message"}` for HTTP errors;
   `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` for 422 validation errors.
   Zero extra code; consistent with FastAPI ecosystem.

B) **Custom envelope** — standardized format across all errors:
   `{"error": {"code": "INVALID_CREDENTIALS", "message": "...", "request_id": "..."}}`.
   Friendlier for API consumers; requires custom exception handler.

[Answer]: A

---

### Q4: CORS middleware

Should CORS middleware be added in Unit 1? Relevant if a browser-based frontend
will call the API during local development.

A) **Add permissive CORS for local dev** — `allow_origins=["*"]` or
   `allow_origins=["http://localhost:3000", "http://localhost:5173"]`.
   Unblocks frontend dev immediately; note in code that this must be tightened for production.

B) **Skip CORS** — API is consumed by server-side clients or curl/Postman only.
   Can always be added later with one middleware line.

[Answer]: A

---

### Q5: Correlation ID source

Request correlation IDs tie together all log entries for a single request.

A) **Always generate** — middleware generates a new UUID4 for every request, regardless
   of request headers. Simple, self-contained; no dependency on client behavior.

B) **Passthrough X-Request-ID** — if the request includes an `X-Request-ID` header, use it;
   otherwise generate one. Enables end-to-end tracing when a gateway or test client sets the header.

[Answer]: A


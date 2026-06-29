# Infrastructure Design Plan — Unit 1: Authentication

## Plan Execution Checklist

- [x] Analyze design artifacts
- [x] Ask clarifying infrastructure questions
- [x] Generate `infrastructure-design.md`
- [x] Generate `deployment-architecture.md`

---

## Scope Note

This project targets **local development only** (confirmed in requirements). No cloud provider,
no load balancer, no API gateway. Infrastructure scope is intentionally minimal.

**Already decided (N/A — no questions needed)**:
- Deployment Environment: Local machine only — no cloud
- Messaging Infrastructure: N/A — no async messaging
- Networking Infrastructure: N/A — no load balancer, no API gateway
- Shared Infrastructure: N/A — single developer, single process

---

## Questions Requiring User Input

### Q1: Run method

A) **uvicorn directly** — `uvicorn main:app --reload`. Zero setup, fast iteration.
   Standard approach for FastAPI local dev.

B) **Docker + docker-compose** — containerized, reproducible environment. Requires
   Docker installed; slightly more setup but environment is portable.

C) **Both** — provide both `uvicorn` direct-run instructions AND a `docker-compose.yml`
   for developers who prefer containers.

[Answer]: A

---

### Q2: Server port

A) **8000** (FastAPI/uvicorn default)

B) **Configurable via environment variable** — `APP_PORT=8000` in `.env`, passed to
   uvicorn on startup. Allows running multiple services locally without port conflicts.

[Answer]: B

---

### Q3: Data directory location

Where should the JSON data files (`users.json`, `tasks.json`) live?

A) **`./data/`** — relative to the project root. Created automatically at startup.
   Simple; works whether you `cd` into the project or run from parent directory.

B) **Configurable via `DATA_DIR` env var** — defaults to `./data/` but can be
   overridden. Allows pointing to a different location (e.g., a shared test fixture dir).

[Answer]: B

---

### Q4: Log output destination

A) **stdout only** — all JSON log lines go to terminal. Redirect with shell if needed:
   `uvicorn main:app 2>&1 | tee app.log`.

B) **stdout + rotating file** — `RotatingFileHandler` writes to `./logs/app.log`,
   max 10MB per file, 3 backups. Useful for reviewing logs after the server runs.

[Answer]: A


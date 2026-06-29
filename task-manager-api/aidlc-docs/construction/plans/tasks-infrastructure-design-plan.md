# Infrastructure Design Plan — Unit 2: Task Management

## Plan Execution Checklist

- [x] Analyze design artifacts
- [x] No new questions — all infrastructure inherited from Unit 1
- [x] Generate `infrastructure-design.md`
- [x] Generate `deployment-architecture.md`

## Inherited from Unit 1 (unchanged)

- Deployment: uvicorn directly, local machine
- Port: APP_PORT env var (default 8000)
- Data directory: DATA_DIR env var (default ./data/)
- Logging: stdout JSON lines
- CORS: permissive for local dev
- Startup validation: JWT_SECRET_KEY + DATA_DIR creation

## Unit 2 Additions

- `data/tasks.json` — new data file, created on first task creation
- `GET /tasks`, `POST /tasks`, `GET /tasks/{id}`, `PUT /tasks/{id}`, `PATCH /tasks/{id}`, `DELETE /tasks/{id}` — 6 new routes
- `GET /users`, `GET /users/{id}` — 2 new routes

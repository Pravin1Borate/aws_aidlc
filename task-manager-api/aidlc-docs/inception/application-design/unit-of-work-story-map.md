# Unit of Work — Story Map

## Summary

| Unit | Stories | Count |
|---|---|---|
| Unit 1: Authentication | US-01, US-02, US-03, US-04 | 4 |
| Unit 2: Task Management | US-05 through US-22 | 18 |
| **Total** | **US-01 to US-22** | **22** |

---

## Unit 1: Authentication

| Story ID | Title | Component | Endpoint |
|---|---|---|---|
| US-01 | Register a new account | AuthRouter → AuthService → UserRepository | `POST /auth/register` |
| US-02 | Log in and receive JWT | AuthRouter → AuthService → SecurityUtils | `POST /auth/login` |
| US-03 | Log out | AuthRouter → AuthService → SecurityUtils (blacklist) | `POST /auth/logout` |
| US-04 | Access protected endpoint without token | `get_current_user` dependency + ErrorHandlers | All protected routes |

---

## Unit 2: Task Management

### Epic 2: Task Management (CRUD)

| Story ID | Title | Component | Endpoint |
|---|---|---|---|
| US-05 | Create a new task | TaskRouter → TaskService → TaskRepository | `POST /tasks` |
| US-06 | View a task by ID | TaskRouter → TaskService → TaskRepository | `GET /tasks/{id}` |
| US-07 | List my tasks | TaskRouter → TaskService → TaskRepository | `GET /tasks` |
| US-08 | Update a task (full replace) | TaskRouter → TaskService → TaskRepository | `PUT /tasks/{id}` |
| US-09 | Partially update a task | TaskRouter → TaskService → TaskRepository | `PATCH /tasks/{id}` |
| US-10 | Delete a task | TaskRouter → TaskService → TaskRepository | `DELETE /tasks/{id}` |

### Epic 3: Task Organisation

| Story ID | Title | Component | Notes |
|---|---|---|---|
| US-11 | Set task priority | TaskService (business rule) → TaskRepository | Field on TaskCreate/TaskPatch |
| US-12 | Set task status | TaskService (business rule) → TaskRepository | Field on TaskCreate/TaskPatch |
| US-13 | Set and track due date | TaskService → TaskRepository | Field on TaskCreate/TaskPatch |
| US-14 | Assign a category to a task | TaskService → TaskRepository | Field on TaskCreate/TaskPatch |
| US-15 | Add and remove tags | TaskService → TaskRepository | Field on TaskCreate/TaskPatch |

### Epic 4: Task Assignment and Collaboration

| Story ID | Title | Component | Notes |
|---|---|---|---|
| US-16 | Assign a task to another user | TaskService → UserRepository (validate assignee) + TaskRepository | `assignee_id` on TaskPatch |
| US-17 | View tasks assigned to me | TaskService.list_accessible() → TaskRepository.find_accessible() | Filter in `GET /tasks` |
| US-18 | Update a task I am assigned to | TaskService (auth check) → TaskRepository | PATCH by assignee |

### Epic 5: Filtering and Discovery

| Story ID | Title | Component | Notes |
|---|---|---|---|
| US-19 | Filter tasks by status | TaskService.list_accessible(status=...) | `?status=` query param |
| US-20 | Filter tasks by priority | TaskService.list_accessible(priority=...) | `?priority=` query param |
| US-21 | Filter tasks by due date | TaskService.list_accessible(due_date=...) | `?due_date=` query param |
| US-22 | Combine multiple filters | TaskService.list_accessible(status, priority, due_date) | AND composition |

### User Discovery (Epic 1 extension — for assignee selection)

| Story | Title | Component | Endpoint |
|---|---|---|---|
| Supporting US-16 | List all users | UserRouter → UserService → UserRepository | `GET /users` |
| Supporting US-16 | Get user by ID | UserRouter → UserService → UserRepository | `GET /users/{id}` |
| Supporting US-04 | Health check | UserRouter | `GET /health` |

---

## Component Coverage Map

| Component | Stories Covered |
|---|---|
| `AuthRouter` | US-01, US-02, US-03 |
| `AuthService` | US-01, US-02, US-03, US-04 |
| `UserRepository` | US-01, US-02, US-04, US-16 (validate assignee) |
| `SecurityUtils` | US-02, US-03, US-04 |
| `get_current_user` dependency | US-04 (and all Unit 2 authenticated stories) |
| `TaskRouter` | US-05 to US-22 |
| `TaskService` | US-05 to US-22 |
| `TaskRepository` | US-05 to US-22 |
| `UserRouter` | Supporting US-16, health check |
| `UserService` | Supporting US-16 |
| `JsonFileStorage` | All data-persisting stories |
| `RateLimiterMiddleware` | All endpoint stories (FR-10) |
| `ErrorHandlers` | All stories (error scenarios) |

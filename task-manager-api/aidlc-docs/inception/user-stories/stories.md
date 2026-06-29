# User Stories

**Organisation**: Feature-based (Epic → Story)
**Acceptance Criteria Format**: Given/When/Then (BDD Gherkin)
**Persona**: User (all registered users)
**Admin scope**: Excluded (MVP — ownership-based access only)

---

## Epic 1: User Authentication

*As a User, I need secure account management so I can access my tasks privately and safely.*

---

### US-01: Register a New Account

**As a** User,
**I want to** create an account with my email and password,
**so that** I can access the Task Manager API.

**Acceptance Criteria**:

```gherkin
Scenario: Successful registration
  Given I am not registered
  When I POST /auth/register with a valid email and password (min 8 chars)
  Then I receive HTTP 201 Created
  And my account is created with a unique UUID
  And my password is stored as a hash (never plain text)
  And I receive a success response with my user ID and email (no password)

Scenario: Duplicate email registration
  Given a user with email "alice@example.com" already exists
  When I POST /auth/register with email "alice@example.com"
  Then I receive HTTP 409 Conflict
  And the response contains a generic error message (no internal details)

Scenario: Invalid email format
  Given I am not registered
  When I POST /auth/register with an invalid email format
  Then I receive HTTP 422 Unprocessable Entity
  And the response identifies the invalid field

Scenario: Password too short
  Given I am not registered
  When I POST /auth/register with a password shorter than 8 characters
  Then I receive HTTP 422 Unprocessable Entity
  And the response indicates the password constraint
```

---

### US-02: Log In and Receive JWT

**As a** User,
**I want to** log in with my email and password,
**so that** I receive a JWT token to authenticate subsequent requests.

**Acceptance Criteria**:

```gherkin
Scenario: Successful login
  Given I have a registered account
  When I POST /auth/login with correct email and password
  Then I receive HTTP 200 OK
  And the response contains a signed JWT access token
  And the token includes my user ID and expiration claim
  And the token is valid for server-side verification on subsequent requests

Scenario: Invalid credentials
  Given I have a registered account
  When I POST /auth/login with an incorrect password
  Then I receive HTTP 401 Unauthorized
  And the response contains a generic "invalid credentials" message
  And no token is issued

Scenario: Non-existent account
  Given no account exists for "unknown@example.com"
  When I POST /auth/login with that email
  Then I receive HTTP 401 Unauthorized
  And the response is identical to an incorrect-password response (no user enumeration)
```

---

### US-03: Log Out

**As a** User,
**I want to** log out of my session,
**so that** my token is no longer usable by others.

**Acceptance Criteria**:

```gherkin
Scenario: Successful logout
  Given I am authenticated with a valid JWT
  When I POST /auth/logout with my token in the Authorization header
  Then I receive HTTP 200 OK
  And subsequent requests using the same token receive HTTP 401 Unauthorized

Scenario: Logout without authentication
  Given I have no token
  When I POST /auth/logout without an Authorization header
  Then I receive HTTP 401 Unauthorized
```

---

### US-04: Access Protected Endpoint Without Token

**As a** system enforcing security,
**I want to** reject unauthenticated requests to protected endpoints,
**so that** task data is never exposed without authentication.

**Acceptance Criteria**:

```gherkin
Scenario: Missing token on protected endpoint
  Given I have no JWT token
  When I make any request to a protected endpoint (e.g., GET /tasks)
  Then I receive HTTP 401 Unauthorized
  And the response does not reveal any task data

Scenario: Expired token
  Given I have a JWT token that has expired
  When I make a request to a protected endpoint
  Then I receive HTTP 401 Unauthorized
  And the response does not reveal any task data
```

---

## Epic 2: Task Management (CRUD)

*As a User, I need to create, view, update, and delete tasks so I can manage my work.*

---

### US-05: Create a New Task

**As a** User,
**I want to** create a new task with a title and optional details,
**so that** I can track a piece of work.

**Acceptance Criteria**:

```gherkin
Scenario: Successful task creation with required fields only
  Given I am authenticated
  When I POST /tasks with a valid title
  Then I receive HTTP 201 Created
  And the response contains a task with a unique UUID
  And status defaults to "todo"
  And priority defaults to "medium"
  And I am set as the owner

Scenario: Successful task creation with all fields
  Given I am authenticated
  When I POST /tasks with title, description, priority "high", status "in_progress",
       due_date "2026-12-31", category "work", tags ["urgent", "review"]
  Then I receive HTTP 201 Created
  And all provided fields are reflected in the response

Scenario: Missing required title
  Given I am authenticated
  When I POST /tasks without a title field
  Then I receive HTTP 422 Unprocessable Entity
  And the response identifies the missing title field

Scenario: Title exceeds maximum length
  Given I am authenticated
  When I POST /tasks with a title longer than 255 characters
  Then I receive HTTP 422 Unprocessable Entity
```

---

### US-06: View a Task by ID

**As a** User,
**I want to** retrieve a specific task by its ID,
**so that** I can see its full details.

**Acceptance Criteria**:

```gherkin
Scenario: Retrieve owned task
  Given I am authenticated and own task "task-uuid-123"
  When I GET /tasks/task-uuid-123
  Then I receive HTTP 200 OK
  And the response contains all task fields

Scenario: Retrieve assigned task
  Given I am authenticated and am the assignee of task "task-uuid-456"
  When I GET /tasks/task-uuid-456
  Then I receive HTTP 200 OK
  And the response contains all task fields

Scenario: Task not owned or assigned
  Given I am authenticated but neither own nor am assigned to "task-uuid-789"
  When I GET /tasks/task-uuid-789
  Then I receive HTTP 403 Forbidden
  And no task data is revealed

Scenario: Non-existent task
  Given I am authenticated
  When I GET /tasks/non-existent-id
  Then I receive HTTP 404 Not Found
```

---

### US-07: List My Tasks

**As a** User,
**I want to** retrieve a list of tasks I own or am assigned to,
**so that** I can get an overview of my work.

**Acceptance Criteria**:

```gherkin
Scenario: List all accessible tasks
  Given I am authenticated and have 3 owned tasks and 2 assigned tasks
  When I GET /tasks with no filters
  Then I receive HTTP 200 OK
  And the response contains all 5 tasks
  And tasks are sorted by due date ascending (tasks without due date last)

Scenario: No tasks exist
  Given I am authenticated and have no owned or assigned tasks
  When I GET /tasks
  Then I receive HTTP 200 OK
  And the response contains an empty list

Scenario: Tasks from other users not returned
  Given I am authenticated as User A
  And User B has tasks not assigned to User A
  When I GET /tasks
  Then the response does NOT include User B's unassigned tasks
```

---

### US-08: Update a Task (Full Replace)

**As a** User,
**I want to** fully replace a task's fields via PUT,
**so that** I can update all properties at once.

**Acceptance Criteria**:

```gherkin
Scenario: Full update of owned task
  Given I am authenticated and own task "task-uuid-123"
  When I PUT /tasks/task-uuid-123 with a complete task body
  Then I receive HTTP 200 OK
  And all fields in the response reflect the new values
  And updated_at is refreshed

Scenario: Unauthorised full update
  Given I am authenticated but do not own task "task-uuid-456"
  And I am not the assignee
  When I PUT /tasks/task-uuid-456
  Then I receive HTTP 403 Forbidden
```

---

### US-09: Partially Update a Task

**As a** User,
**I want to** update individual fields of a task via PATCH,
**so that** I can make targeted changes without resending the entire task.

**Acceptance Criteria**:

```gherkin
Scenario: Partial update by owner
  Given I am authenticated and own task "task-uuid-123"
  When I PATCH /tasks/task-uuid-123 with only {"status": "done"}
  Then I receive HTTP 200 OK
  And only the status field is updated
  And all other fields remain unchanged

Scenario: Partial update by assignee
  Given I am authenticated and am the assignee of task "task-uuid-456"
  When I PATCH /tasks/task-uuid-456 with {"status": "in_progress"}
  Then I receive HTTP 200 OK
  And the status is updated

Scenario: Idempotent PATCH — applying same update twice
  Given I PATCH task "task-uuid-123" with {"priority": "high"}
  When I PATCH the same task with {"priority": "high"} again
  Then I receive HTTP 200 OK
  And the task state is identical to after the first PATCH

Scenario: Invalid field value
  Given I am authenticated and own a task
  When I PATCH with {"priority": "critical"} (invalid value)
  Then I receive HTTP 422 Unprocessable Entity
```

---

### US-10: Delete a Task

**As a** User,
**I want to** delete a task I own,
**so that** I can remove tasks that are no longer relevant.

**Acceptance Criteria**:

```gherkin
Scenario: Successful deletion by owner
  Given I am authenticated and own task "task-uuid-123"
  When I DELETE /tasks/task-uuid-123
  Then I receive HTTP 204 No Content
  And subsequent GET /tasks/task-uuid-123 returns HTTP 404

Scenario: Idempotent delete — deleting already deleted task
  Given task "task-uuid-123" has already been deleted
  When I DELETE /tasks/task-uuid-123
  Then I receive HTTP 404 Not Found

Scenario: Delete by assignee (not owner) — forbidden
  Given I am the assignee but not the owner of task "task-uuid-456"
  When I DELETE /tasks/task-uuid-456
  Then I receive HTTP 403 Forbidden
  And the task still exists
```

---

## Epic 3: Task Organisation

*As a User, I need to organise tasks with priority, status, due dates, categories, and tags so I can manage my workload effectively.*

---

### US-11: Set Task Priority

**As a** User,
**I want to** set the priority of a task to Low, Medium, or High,
**so that** I can indicate its importance.

**Acceptance Criteria**:

```gherkin
Scenario: Set priority on creation
  Given I am authenticated
  When I POST /tasks with priority "high"
  Then the created task has priority "high"

Scenario: Update priority via PATCH
  Given I own a task with priority "low"
  When I PATCH /tasks/{id} with {"priority": "medium"}
  Then the task priority is updated to "medium"

Scenario: Default priority
  Given I POST /tasks without specifying priority
  Then the created task has priority "medium"

Scenario: Invalid priority value
  When I submit a task with priority "critical"
  Then I receive HTTP 422 Unprocessable Entity
```

---

### US-12: Set Task Status

**As a** User,
**I want to** set and update the status of a task (Todo / In Progress / Done),
**so that** I can track its progress.

**Acceptance Criteria**:

```gherkin
Scenario: Default status on creation
  Given I POST /tasks without specifying status
  Then the created task has status "todo"

Scenario: Update status to in_progress
  Given I own or am assigned to a task with status "todo"
  When I PATCH /tasks/{id} with {"status": "in_progress"}
  Then the task status is "in_progress"

Scenario: Mark task as done
  Given I own or am assigned to a task
  When I PATCH /tasks/{id} with {"status": "done"}
  Then the task status is "done"

Scenario: Invalid status value
  When I PATCH with {"status": "cancelled"}
  Then I receive HTTP 422 Unprocessable Entity
```

---

### US-13: Set and Track Due Date

**As a** User,
**I want to** set a due date on a task,
**so that** I can track deadlines.

**Acceptance Criteria**:

```gherkin
Scenario: Set due date on creation
  Given I POST /tasks with due_date "2026-12-31"
  Then the created task has due_date "2026-12-31"

Scenario: Update due date via PATCH
  Given I own a task
  When I PATCH /tasks/{id} with {"due_date": "2026-11-30"}
  Then the task due_date is updated

Scenario: Clear due date
  Given I own a task with a due date
  When I PATCH /tasks/{id} with {"due_date": null}
  Then the task due_date is null

Scenario: Invalid date format
  When I submit a task with due_date "31/12/2026" (non-ISO format)
  Then I receive HTTP 422 Unprocessable Entity
```

---

### US-14: Assign a Category to a Task

**As a** User,
**I want to** assign a single category label to a task,
**so that** I can group related tasks together.

**Acceptance Criteria**:

```gherkin
Scenario: Assign category on creation
  Given I POST /tasks with category "work"
  Then the created task has category "work"

Scenario: Update category via PATCH
  Given I own a task with category "personal"
  When I PATCH /tasks/{id} with {"category": "work"}
  Then the task category is updated to "work"

Scenario: Remove category
  Given I own a task with a category
  When I PATCH /tasks/{id} with {"category": null}
  Then the task has no category

Scenario: Category exceeds max length
  When I submit a task with a category string longer than 100 characters
  Then I receive HTTP 422 Unprocessable Entity
```

---

### US-15: Add and Remove Tags

**As a** User,
**I want to** add multiple tags to a task,
**so that** I can label tasks with multiple descriptive terms.

**Acceptance Criteria**:

```gherkin
Scenario: Add tags on creation
  Given I POST /tasks with tags ["urgent", "review", "q4"]
  Then the created task has all three tags

Scenario: Replace all tags via PATCH
  Given I own a task with tags ["urgent"]
  When I PATCH /tasks/{id} with {"tags": ["review", "q4"]}
  Then the task tags are ["review", "q4"]

Scenario: Clear all tags
  Given I own a task with tags
  When I PATCH /tasks/{id} with {"tags": []}
  Then the task has no tags

Scenario: Tag exceeds max length
  When I submit a task with a tag string longer than 50 characters
  Then I receive HTTP 422 Unprocessable Entity

Scenario: No tags (default)
  Given I POST /tasks without specifying tags
  Then the created task has an empty tags list
```

---

## Epic 4: Task Assignment and Collaboration

*As a User, I need to assign tasks to colleagues and manage tasks assigned to me.*

---

### US-16: Assign a Task to Another User

**As a** User (task owner),
**I want to** assign my task to another registered user,
**so that** they can work on it.

**Acceptance Criteria**:

```gherkin
Scenario: Assign task to a valid user
  Given I am authenticated and own task "task-uuid-123"
  And user "bob@example.com" is a registered user with ID "bob-uuid"
  When I PATCH /tasks/task-uuid-123 with {"assignee_id": "bob-uuid"}
  Then I receive HTTP 200 OK
  And the task assignee_id is "bob-uuid"

Scenario: Assign to non-existent user
  Given I own a task
  When I PATCH with {"assignee_id": "non-existent-uuid"}
  Then I receive HTTP 422 Unprocessable Entity

Scenario: Assign by non-owner
  Given I am the assignee but not the owner of a task
  When I PATCH the task with {"assignee_id": "another-uuid"}
  Then I receive HTTP 403 Forbidden

Scenario: Unassign a task
  Given I am the owner and the task has an assignee
  When I PATCH with {"assignee_id": null}
  Then the task assignee_id is null
```

---

### US-17: View Tasks Assigned to Me

**As a** User,
**I want to** see tasks that have been assigned to me,
**so that** I know what I'm expected to work on.

**Acceptance Criteria**:

```gherkin
Scenario: List tasks includes assigned tasks
  Given I am authenticated and am the assignee of 2 tasks owned by other users
  When I GET /tasks
  Then the response includes those 2 assigned tasks alongside my owned tasks

Scenario: Assigned tasks from other users are visible
  Given User A owns a task and assigns it to me
  When I GET /tasks
  Then I can see User A's task in my list

Scenario: Assigned tasks respect access control
  Given User A's task is not assigned to me
  When I GET /tasks
  Then User A's task does NOT appear in my list
```

---

### US-18: Update a Task I Am Assigned To

**As a** User (assignee),
**I want to** update the status and details of a task assigned to me,
**so that** I can reflect my progress.

**Acceptance Criteria**:

```gherkin
Scenario: Assignee updates task status
  Given I am the assignee of task "task-uuid-456"
  When I PATCH /tasks/task-uuid-456 with {"status": "in_progress"}
  Then I receive HTTP 200 OK
  And the status is updated

Scenario: Assignee cannot delete the task
  Given I am the assignee but not the owner
  When I DELETE /tasks/{id}
  Then I receive HTTP 403 Forbidden
```

---

## Epic 5: Filtering and Discovery

*As a User, I need to filter my task list so I can focus on the tasks that matter right now.*

---

### US-19: Filter Tasks by Status

**As a** User,
**I want to** filter my task list by status,
**so that** I can focus on tasks in a particular state.

**Acceptance Criteria**:

```gherkin
Scenario: Filter by single status
  Given I have tasks with statuses "todo", "in_progress", and "done"
  When I GET /tasks?status=todo
  Then I receive only tasks with status "todo"

Scenario: No tasks match filter
  Given I have no tasks with status "done"
  When I GET /tasks?status=done
  Then I receive HTTP 200 OK with an empty list

Scenario: Invalid status filter value
  When I GET /tasks?status=cancelled
  Then I receive HTTP 422 Unprocessable Entity
```

---

### US-20: Filter Tasks by Priority

**As a** User,
**I want to** filter my task list by priority level,
**so that** I can focus on urgent or low-priority tasks.

**Acceptance Criteria**:

```gherkin
Scenario: Filter by priority
  Given I have tasks with priorities "low", "medium", and "high"
  When I GET /tasks?priority=high
  Then I receive only tasks with priority "high"

Scenario: Invalid priority filter value
  When I GET /tasks?priority=critical
  Then I receive HTTP 422 Unprocessable Entity
```

---

### US-21: Filter Tasks by Due Date

**As a** User,
**I want to** filter tasks by due date,
**so that** I can see what is due on or before a specific date.

**Acceptance Criteria**:

```gherkin
Scenario: Filter tasks due on or before a date
  Given I have tasks with due dates "2026-07-01", "2026-08-15", and no due date
  When I GET /tasks?due_date=2026-07-31
  Then I receive only the task with due_date "2026-07-01"
  And tasks without a due date are excluded

Scenario: Invalid due date format
  When I GET /tasks?due_date=31-12-2026
  Then I receive HTTP 422 Unprocessable Entity
```

---

### US-22: Combine Multiple Filters

**As a** User,
**I want to** combine status, priority, and due date filters,
**so that** I can narrow down my task list precisely.

**Acceptance Criteria**:

```gherkin
Scenario: Combined status and priority filter
  Given I have various tasks
  When I GET /tasks?status=todo&priority=high
  Then I receive only tasks that are both "todo" AND "high" priority

Scenario: All filters combined
  When I GET /tasks?status=in_progress&priority=medium&due_date=2026-12-31
  Then I receive only tasks matching all three filter criteria simultaneously
```

---

## Story Summary

| Epic | Stories | Count |
|---|---|---|
| Epic 1: User Authentication | US-01 to US-04 | 4 |
| Epic 2: Task Management (CRUD) | US-05 to US-10 | 6 |
| Epic 3: Task Organisation | US-11 to US-15 | 5 |
| Epic 4: Task Assignment & Collaboration | US-16 to US-18 | 3 |
| Epic 5: Filtering & Discovery | US-19 to US-22 | 4 |
| **Total** | **US-01 to US-22** | **22** |

## INVEST Compliance

| Criterion | Status | Notes |
|---|---|---|
| **Independent** | Compliant | Each story can be implemented and tested in isolation |
| **Negotiable** | Compliant | Stories describe what, not how — implementation details deferred to design |
| **Valuable** | Compliant | Every story delivers direct user value |
| **Estimable** | Compliant | All stories are scoped to a single API feature or endpoint group |
| **Small** | Compliant | Each story fits within a single sprint iteration |
| **Testable** | Compliant | All stories have Given/When/Then acceptance criteria |

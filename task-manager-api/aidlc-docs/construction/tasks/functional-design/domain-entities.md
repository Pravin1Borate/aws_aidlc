# Domain Entities — Unit 2: Task Management

## Entity: Task

**Description**: The core domain object. Represents a unit of work with lifecycle management, ownership, assignment, and organisational metadata.

### Fields

| Field | Type | Constraints | Default |
|---|---|---|---|
| `id` | str (UUID) | System-generated, immutable, unique | `uuid4()` on creation |
| `title` | str | Required, max 255 chars | — |
| `description` | str \| None | Optional, max 2000 chars | `None` |
| `status` | TaskStatus | Enum: `todo`, `in_progress`, `done` | `todo` |
| `priority` | TaskPriority | Enum: `low`, `medium`, `high` | `medium` |
| `due_date` | date \| None | Optional, ISO 8601 date (YYYY-MM-DD). Past dates accepted silently. | `None` |
| `category` | str \| None | Optional, max 100 chars, free-form | `None` |
| `tags` | list[str] | Optional, each tag max 50 chars, no exact duplicates | `[]` |
| `owner_id` | str (UUID) | Set to creator's ID on creation, **immutable** | caller's `user_id` |
| `assignee_id` | str \| None (UUID) | Optional reference to a registered user | `None` |
| `deleted_at` | datetime \| None | Soft delete timestamp (UTC). `None` = active. | `None` |
| `created_at` | datetime | UTC, immutable, set on creation | `utcnow()` on creation |
| `updated_at` | datetime | UTC, updated on every write | `utcnow()` on each write |

### Business Invariants
- `status` is always one of `{todo, in_progress, done}`
- `priority` is always one of `{low, medium, high}`
- `owner_id` never changes after creation
- `tags` contains no exact duplicates (case-sensitive deduplication applied on write)
- `deleted_at` is either `None` (active) or a UTC datetime (soft-deleted)
- A soft-deleted task (`deleted_at is not None`) is treated as non-existent for all read/write operations

### Persistence
- Stored as JSON objects in `data/tasks.json`
- `deleted_at` is persisted — soft-deleted records remain in storage, filtered at query time
- `assignee_id` stores only the resolved UUID (email resolution happens before persistence)

---

## Value Objects

### TaskStatus
- **Type**: Python `enum.Enum`
- **Values**: `todo`, `in_progress`, `done`
- **Default**: `todo` on task creation
- **Transitions**: Any status transition is allowed (no enforced state machine in MVP)

### TaskPriority
- **Type**: Python `enum.Enum`
- **Values**: `low`, `medium`, `high`
- **Default**: `medium` on task creation

### TaskFilter (query parameter object, not persisted)
- `status: TaskStatus | None`
- `priority: TaskPriority | None`
- `due_date: date | None` — returns tasks due on or before this date

### AssigneeRef (input-only, not persisted)
- Used in `TaskCreate` and `TaskUpdate` inputs to support dual-format assignment (Q4=C)
- `assignee_id: str | None` — UUID of registered user (takes precedence if both provided)
- `assignee_email: str | None` — email of registered user (server resolves to UUID)
- Resolution order: `assignee_id` first; `assignee_email` if `assignee_id` absent
- Resolved to `assignee_id` UUID before task persistence

---

## Entity: UserSummary (read-only projection for /users endpoints)

**Description**: A lightweight, read-only projection of a User — used by the `/users` endpoint to support assignee lookup. The full User entity is owned by Unit 1 (`auth/repository.py`); this projection is computed by `UserService` in Unit 2 from the shared `users.json`.

### Fields

| Field | Type | Notes |
|---|---|---|
| `id` | str (UUID) | User's unique ID |
| `email` | str | User's email (for display and lookup) |
| `full_name` | str \| None | Optional display name |

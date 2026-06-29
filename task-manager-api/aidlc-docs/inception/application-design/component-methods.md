# Component Methods

**Note**: This document defines method signatures and high-level purpose only. Detailed business rules, validation logic, and algorithms are specified in Functional Design (CONSTRUCTION phase, per unit).

---

## AuthService (`auth/service.py`)

```python
class AuthService:
    def __init__(self, user_repo: UserRepository, security: SecurityUtils): ...

    async def register(self, data: UserCreate) -> UserResponse:
        """Create a new user account. Raises ConflictError if email exists."""

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Verify credentials and issue a signed JWT. Raises UnauthorizedError on failure."""

    async def logout(self, token: str) -> None:
        """Blacklist the given token. Raises UnauthorizedError if token is invalid."""

    async def get_current_user(self, token: str) -> UserResponse:
        """Validate token and return the authenticated user. Raises UnauthorizedError if invalid/expired."""
```

---

## UserRepository (`auth/repository.py`)

```python
class UserRepository:
    def __init__(self, storage: JsonFileStorage): ...

    async def find_by_email(self, email: str) -> User | None:
        """Return User with matching email, or None if not found."""

    async def find_by_id(self, user_id: UUID) -> User | None:
        """Return User with matching ID, or None if not found."""

    async def save(self, user: User) -> User:
        """Persist a new user. Returns the saved user."""

    async def list_all(self) -> list[User]:
        """Return all registered users."""
```

---

## TaskService (`tasks/service.py`)

```python
class TaskService:
    def __init__(self, task_repo: TaskRepository, user_repo: UserRepository): ...

    async def create(self, data: TaskCreate, owner_id: UUID) -> TaskResponse:
        """Create a new task owned by owner_id."""

    async def get_by_id(self, task_id: UUID, caller_id: UUID) -> TaskResponse:
        """Return task if caller is owner or assignee. Raises NotFoundError or ForbiddenError."""

    async def list_accessible(
        self,
        caller_id: UUID,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        due_date: date | None,
    ) -> list[TaskResponse]:
        """Return all tasks owned by or assigned to caller, with optional filters applied."""

    async def full_update(self, task_id: UUID, data: TaskUpdate, caller_id: UUID) -> TaskResponse:
        """Replace all task fields. Caller must be owner. Raises ForbiddenError otherwise."""

    async def partial_update(self, task_id: UUID, data: TaskPatch, caller_id: UUID) -> TaskResponse:
        """Update only provided fields. Caller must be owner or assignee. Raises ForbiddenError otherwise."""

    async def delete(self, task_id: UUID, caller_id: UUID) -> None:
        """Delete task. Caller must be owner. Raises ForbiddenError otherwise."""
```

---

## TaskRepository (`tasks/repository.py`)

```python
class TaskRepository:
    def __init__(self, storage: JsonFileStorage): ...

    async def find_by_id(self, task_id: UUID) -> Task | None:
        """Return Task with matching ID, or None."""

    async def find_accessible(self, user_id: UUID) -> list[Task]:
        """Return all tasks where owner_id == user_id OR assignee_id == user_id."""

    async def save(self, task: Task) -> Task:
        """Persist a new task. Returns the saved task."""

    async def update(self, task: Task) -> Task:
        """Persist updated task. Returns the updated task."""

    async def delete(self, task_id: UUID) -> None:
        """Remove task by ID."""
```

---

## UserService (`users/service.py`)

```python
class UserService:
    def __init__(self, user_repo: UserRepository): ...

    async def list_users(self) -> list[UserPublicResponse]:
        """Return all users with public fields only (no password hashes)."""

    async def get_user(self, user_id: UUID) -> UserPublicResponse:
        """Return public user profile. Raises NotFoundError if not found."""
```

---

## JsonFileStorage (`core/storage.py`)

```python
class JsonFileStorage:
    def __init__(self, file_path: Path): ...

    def read_all(self) -> list[dict]:
        """Read and return all records from the JSON file."""

    def write_all(self, records: list[dict]) -> None:
        """Atomically overwrite the JSON file with the provided records."""

    def find_by_id(self, record_id: str) -> dict | None:
        """Return first record matching 'id' field, or None."""

    def upsert(self, record: dict) -> dict:
        """Insert or update a record by 'id'. Returns the saved record."""

    def delete_by_id(self, record_id: str) -> bool:
        """Remove record by 'id'. Returns True if deleted, False if not found."""
```

---

## SecurityUtils (`core/security.py`)

```python
def hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt. Returns the hash string."""

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""

def create_access_token(payload: dict, expiry_minutes: int) -> str:
    """Create a signed JWT with the given payload and expiration."""

def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT. Raises UnauthorizedError if invalid or expired."""

def is_token_blacklisted(token: str) -> bool:
    """Return True if the token has been blacklisted (logged out)."""

def blacklist_token(token: str) -> None:
    """Add token to the blacklist set."""
```

---

## RateLimiter (`core/rate_limiter.py`)

```python
class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        authenticated_limit: int,   # requests per minute for authenticated users
        unauthenticated_limit: int,  # requests per minute per IP
    ): ...

    async def dispatch(self, request: Request, call_next) -> Response:
        """Check rate limit for request. Return 429 with Retry-After if exceeded."""
```

---

## ErrorHandlers (`core/errors.py`)

```python
class AppException(Exception):
    def __init__(self, status_code: int, message: str): ...

class NotFoundError(AppException): ...       # 404
class ForbiddenError(AppException): ...      # 403
class UnauthorizedError(AppException): ...   # 401
class ConflictError(AppException): ...       # 409
class ValidationError(AppException): ...     # 422

def register_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app.
    All handlers return generic messages — no stack traces or internal details."""
```

---

## FastAPI Dependencies (`dependencies.py`)

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Resolve the authenticated user from the Bearer token.
    Raises HTTP 401 if token is missing, invalid, expired, or blacklisted."""

async def get_auth_service() -> AuthService:
    """Dependency factory — construct and return an AuthService instance."""

async def get_task_service() -> TaskService:
    """Dependency factory — construct and return a TaskService instance."""

async def get_user_service() -> UserService:
    """Dependency factory — construct and return a UserService instance."""
```

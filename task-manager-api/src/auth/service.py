import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError

from src.auth.repository import UserRepository
from src.auth.schemas import LoginRequest, TokenResponse, User, UserCreate, UserResponse
from src.config import settings
from src.core.errors import ConflictError, UnauthorizedError
from src.core.security import (
    blacklist_token,
    create_access_token,
    decode_access_token,
    get_dummy_hash,
    is_blacklisted,
    verify_password,
    hash_password,
)

_LOCKOUT_THRESHOLD = 5
_LOCKOUT_DURATION = timedelta(minutes=15)


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._repo = user_repo

    def register(self, data: UserCreate) -> UserResponse:
        if self._repo.find_by_email(data.email) is not None:
            raise ConflictError("An account with this email already exists")
        now = datetime.now(timezone.utc)
        user = User(
            id=str(uuid.uuid4()),
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            failed_login_attempts=0,
            lockout_until=None,
            created_at=now,
            updated_at=now,
        )
        self._repo.save(user)
        return _to_response(user)

    def login(self, data: LoginRequest) -> TokenResponse:
        user = self._repo.find_by_email(data.email)
        if user is None:
            # Run dummy verify to prevent timing-based user enumeration.
            verify_password(data.password, get_dummy_hash())
            raise UnauthorizedError("Invalid credentials")

        now = datetime.now(timezone.utc)
        if user.lockout_until and user.lockout_until > now:
            raise UnauthorizedError("Account is temporarily locked")

        if not verify_password(data.password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= _LOCKOUT_THRESHOLD:
                user.lockout_until = now + _LOCKOUT_DURATION
            user.updated_at = now
            self._repo.save(user)
            raise UnauthorizedError("Invalid credentials")

        user.failed_login_attempts = 0
        user.lockout_until = None
        user.updated_at = now
        self._repo.save(user)

        token = create_access_token({"sub": user.id, "email": user.email})
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRY_MINUTES * 60,
        )

    def logout(self, token: str) -> None:
        self._validate_token(token)
        blacklist_token(token)

    def get_current_user(self, token: str) -> UserResponse:
        payload = self._validate_token(token)
        user = self._repo.find_by_id(payload.get("sub", ""))
        if user is None:
            raise UnauthorizedError("Invalid token")
        return _to_response(user)

    def _validate_token(self, token: str) -> dict:
        try:
            payload = decode_access_token(token)
        except JWTError:
            raise UnauthorizedError("Invalid token")
        if is_blacklisted(token):
            raise UnauthorizedError("Invalid token")
        return payload


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
    )

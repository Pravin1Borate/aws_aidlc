import bcrypt
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError

_blacklist: set[str] = set()

# Pre-computed dummy hash used to keep response timing consistent when user is not found.
_DUMMY_HASH: str = bcrypt.hashpw(b"dummy_timing_guard", bcrypt.gensalt(rounds=12)).decode()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    from src.config import settings

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    )
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.now(timezone.utc)
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    from src.config import settings

    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])


def blacklist_token(token: str) -> None:
    _blacklist.add(token)


def is_blacklisted(token: str) -> bool:
    return token in _blacklist


def get_dummy_hash() -> str:
    return _DUMMY_HASH

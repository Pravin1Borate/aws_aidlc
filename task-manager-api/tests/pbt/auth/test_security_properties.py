import tempfile

import pytest
from hypothesis import HealthCheck, given, settings as h_settings, assume
from hypothesis import strategies as st

from src.core import security


# Reusable strategy for valid passwords (8–128 printable ASCII, no null bytes)
valid_passwords = st.text(
    alphabet=st.characters(min_codepoint=32, max_codepoint=126),
    min_size=8,
    max_size=128,
)

# Strategy for valid email-like sub claims
user_ids = st.uuids().map(str)


@pytest.mark.pbt
class TestPasswordProperties:
    @given(password=valid_passwords)
    @h_settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_password_hash_roundtrip(self, password: str, patch_settings):
        """Property 1: verify(p, hash(p)) is always True (PBT-02 round-trip)."""
        hashed = security.hash_password(password)
        assert security.verify_password(password, hashed) is True

    @given(
        password=valid_passwords,
        wrong=valid_passwords,
    )
    @h_settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_wrong_password_never_verifies(self, password: str, wrong: str, patch_settings):
        """Property 2: verify(w, hash(p)) is False when w != p (PBT-02 round-trip inverse)."""
        assume(password != wrong)
        hashed = security.hash_password(password)
        assert security.verify_password(wrong, hashed) is False


@pytest.mark.pbt
class TestJWTProperties:
    @given(user_id=user_ids, email=st.emails())
    @h_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_jwt_roundtrip(self, user_id: str, email: str, patch_settings):
        """Property 3: decoded payload contains all keys from original dict (PBT-02 round-trip)."""
        original = {"sub": user_id, "email": email}
        token = security.create_access_token(original)
        decoded = security.decode_access_token(token)
        assert decoded["sub"] == user_id
        assert decoded["email"] == email


@pytest.mark.pbt
class TestBlacklistProperties:
    @given(token=st.text(min_size=10, max_size=200))
    @h_settings(max_examples=50)
    def test_blacklist_idempotent(self, token: str):
        """Property 4: blacklisting a token twice has same effect as once (PBT-04 idempotence)."""
        security._blacklist.clear()
        security.blacklist_token(token)
        state_after_one = security.is_blacklisted(token)
        security.blacklist_token(token)
        state_after_two = security.is_blacklisted(token)
        assert state_after_one == state_after_two is True


@pytest.mark.pbt
class TestInvariantProperties:
    @given(
        failure_count=st.integers(min_value=0, max_value=10),
    )
    @h_settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_failed_login_counter_never_negative(self, failure_count: int, patch_settings):
        """Property 5: failed_login_attempts invariant — counter is always >= 0 (PBT-03)."""
        from src.auth.service import AuthService
        from src.auth.repository import UserRepository
        from src.auth.schemas import UserCreate, LoginRequest
        from src.core.storage import JsonFileStorage

        with tempfile.TemporaryDirectory() as tmp:
            storage = JsonFileStorage(f"{tmp}/users.json")
            repo = UserRepository(storage)
            svc = AuthService(repo)
            svc.register(UserCreate(email="test@example.com", password="password123"))

            for _ in range(failure_count):
                try:
                    svc.login(LoginRequest(email="test@example.com", password="wrong"))
                except Exception:
                    pass

            user = repo.find_by_email("test@example.com")
            assert user.failed_login_attempts >= 0

    @given(email_prefix=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    @h_settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_email_normalization_invariant(self, email_prefix: str, patch_settings):
        """Property 6: stored email is always lowercase (PBT-03 invariant)."""
        from src.auth.service import AuthService
        from src.auth.repository import UserRepository
        from src.auth.schemas import UserCreate
        from src.core.storage import JsonFileStorage

        email = f"{email_prefix}@example.com"
        with tempfile.TemporaryDirectory() as tmp:
            storage = JsonFileStorage(f"{tmp}/users.json")
            repo = UserRepository(storage)
            svc = AuthService(repo)
            svc.register(UserCreate(email=email.upper(), password="password123"))

            user = repo.find_by_email(email.lower())
            assert user is not None
            assert user.email == email.lower()

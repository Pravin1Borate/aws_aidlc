import pytest
from datetime import timedelta
from jose import JWTError

from src.core import security


@pytest.mark.unit
class TestPasswordHashing:
    def test_hash_password_produces_valid_bcrypt_hash(self):
        hashed = security.hash_password("password123")
        assert hashed.startswith("$2b$")

    def test_verify_password_correct_plain(self):
        plain = "mysecretpassword"
        hashed = security.hash_password(plain)
        assert security.verify_password(plain, hashed) is True

    def test_verify_password_wrong_plain(self):
        hashed = security.hash_password("correctpassword")
        assert security.verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        plain = "samepassword"
        h1 = security.hash_password(plain)
        h2 = security.hash_password(plain)
        assert h1 != h2


@pytest.mark.unit
class TestJWT:
    def test_create_access_token_contains_expected_claims(self, patch_settings):
        token = security.create_access_token({"sub": "user-123", "email": "a@b.com"})
        payload = security.decode_access_token(token)
        assert payload["sub"] == "user-123"
        assert payload["email"] == "a@b.com"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_valid_token(self, patch_settings):
        token = security.create_access_token({"sub": "u1"})
        payload = security.decode_access_token(token)
        assert payload["sub"] == "u1"

    def test_decode_expired_token_raises(self, patch_settings):
        token = security.create_access_token(
            {"sub": "u1"}, expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(JWTError):
            security.decode_access_token(token)

    def test_decode_tampered_token_raises(self, patch_settings):
        token = security.create_access_token({"sub": "u1"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            security.decode_access_token(tampered)


@pytest.mark.unit
class TestBlacklist:
    def test_blacklist_token_marks_as_blacklisted(self):
        security.blacklist_token("token-abc")
        assert security.is_blacklisted("token-abc") is True

    def test_blacklist_idempotent(self):
        security.blacklist_token("token-xyz")
        security.blacklist_token("token-xyz")
        assert security.is_blacklisted("token-xyz") is True

    def test_is_blacklisted_returns_false_for_unknown_token(self):
        assert security.is_blacklisted("never-seen-token") is False

    def test_blacklist_does_not_affect_other_tokens(self):
        security.blacklist_token("token-a")
        assert security.is_blacklisted("token-b") is False

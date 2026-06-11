from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings
from app.core.jwt import decode_and_validate

import pytest


class TestDecodeAndValidate:
    def _make_token(self, sub: str = "42", role: str = "user", exp_delta: timedelta | None = None) -> str:
        now = datetime.now(timezone.utc)
        if exp_delta is None:
            exp_delta = timedelta(hours=1)

        payload = {
            "sub": sub,
            "role": role,
            "iat": now,
            "exp": now + exp_delta,
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

    def test_valid_token(self):
        token = self._make_token(sub="42", role="user")
        payload = decode_and_validate(token)

        assert payload["sub"] == "42"
        assert payload["role"] == "user"

    def test_admin_role(self):
        token = self._make_token(sub="1", role="admin")
        payload = decode_and_validate(token)

        assert payload["sub"] == "1"
        assert payload["role"] == "admin"

    def test_expired_token_raises(self):
        token = self._make_token(exp_delta=timedelta(seconds=-10))

        with pytest.raises(ValueError, match="expired"):
            decode_and_validate(token)

    def test_invalid_token_raises(self):
        with pytest.raises(ValueError, match="Invalid token"):
            decode_and_validate("garbage.token.string")

    def test_wrong_secret_raises(self):
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "42",
            "role": "user",
            "iat": now,
            "exp": now + timedelta(hours=1),
        }
        token = jwt.encode(payload, "wrong_secret", algorithm="HS256")

        with pytest.raises(ValueError, match="Invalid token"):
            decode_and_validate(token)

    def test_missing_sub_raises(self):
        now = datetime.now(timezone.utc)
        payload = {
            "role": "user",
            "iat": now,
            "exp": now + timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

        with pytest.raises(ValueError):
            decode_and_validate(token)

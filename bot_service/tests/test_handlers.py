from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from jose import jwt

from app.bot.handlers import cmd_start, cmd_token, handle_text
from app.core.config import settings

import pytest


def _make_token(sub: str = "42", role: str = "user", exp_delta: timedelta | None = None) -> str:
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


class TestStartCommand:
    async def test_start_sends_welcome(self, mock_message):
        msg = mock_message(text="/start")
        await cmd_start(msg)
        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "Привет" in call_text


class TestTokenCommand:
    async def test_token_no_argument(self, mock_message):
        msg = mock_message(text="/token")
        await cmd_token(msg)
        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "Использование" in call_text

    async def test_token_invalid_jwt(self, mock_message):
        msg = mock_message(text="/token garbage_token")
        await cmd_token(msg)
        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "Невалидный" in call_text

    async def test_token_valid_jwt_saved(self, mock_message, fake_redis):
        token = _make_token(sub="42", role="user")
        msg = mock_message(text=f"/token {token}", user_id=99999)

        await cmd_token(msg)

        saved = await fake_redis.get("token:99999")
        assert saved == token

        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "принят" in call_text
        assert "42" in call_text

    async def test_token_expired_jwt_rejected(self, mock_message, fake_redis):
        token = _make_token(exp_delta=timedelta(seconds=-10))
        msg = mock_message(text=f"/token {token}", user_id=88888)

        await cmd_token(msg)

        saved = await fake_redis.get("token:88888")
        assert saved is None

        call_text = msg.answer.call_args[0][0]
        assert "Невалидный" in call_text


class TestHandleText:
    async def test_no_token_stored(self, mock_message):
        msg = mock_message(text="What is Python?", user_id=11111)

        await handle_text(msg)

        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "нет сохранённого токена" in call_text

    async def test_expired_token_removed(self, mock_message, fake_redis):
        expired_token = _make_token(exp_delta=timedelta(seconds=-10))
        await fake_redis.set("token:22222", expired_token)

        msg = mock_message(text="Hello", user_id=22222)

        await handle_text(msg)

        saved = await fake_redis.get("token:22222")
        assert saved is None

        call_text = msg.answer.call_args[0][0]
        assert "истёк" in call_text

    @patch("app.bot.handlers.llm_request")
    async def test_valid_token_sends_to_celery(self, mock_celery, mock_message, fake_redis):
        token = _make_token(sub="42", role="user")
        await fake_redis.set("token:33333", token)

        msg = mock_message(text="Explain AI", user_id=33333, chat_id=33333)

        await handle_text(msg)

        mock_celery.delay.assert_called_once_with(33333, "Explain AI")

        msg.answer.assert_called_once()
        call_text = msg.answer.call_args[0][0]
        assert "принят" in call_text

    @patch("app.bot.handlers.llm_request")
    async def test_empty_text_rejected(self, mock_celery, mock_message):
        msg = mock_message(user_id=44444)
        msg.text = None

        await handle_text(msg)

        mock_celery.delay.assert_not_called()
        call_text = msg.answer.call_args[0][0]
        assert "текстовое" in call_text

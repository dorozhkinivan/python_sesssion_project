from unittest.mock import AsyncMock, MagicMock

import fakeredis.aioredis
import pytest


@pytest.fixture
def fake_redis():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture(autouse=True)
def patch_redis(fake_redis, monkeypatch):
    monkeypatch.setattr("app.bot.handlers.get_redis", lambda: fake_redis)


@pytest.fixture
def mock_message():

    def _create(
        text: str = "Hello",
        user_id: int = 12345,
        chat_id: int = 12345,
        first_name: str = "Test",
    ):
        message = AsyncMock()
        message.text = text
        message.answer = AsyncMock()

        message.from_user = MagicMock()
        message.from_user.id = user_id
        message.from_user.first_name = first_name

        message.chat = MagicMock()
        message.chat.id = chat_id

        return message

    return _create

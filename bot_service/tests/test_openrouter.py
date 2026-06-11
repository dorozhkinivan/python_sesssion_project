import pytest
import respx
from httpx import Response

from app.services.openrouter_client import call_openrouter


class TestOpenRouterClient:
    @respx.mock
    async def test_successful_response(self):
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "Python is a programming language."
                    }
                }
            ]
        }

        respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=Response(200, json=mock_response)
        )

        result = await call_openrouter("What is Python?")
        assert result == "Python is a programming language."

    @respx.mock
    async def test_api_error_status(self):
        respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=Response(500, text="Internal Server Error")
        )

        with pytest.raises(RuntimeError, match="500"):
            await call_openrouter("test prompt")

    @respx.mock
    async def test_malformed_response(self):
        respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=Response(200, json={"unexpected": "format"})
        )

        with pytest.raises(RuntimeError, match="Unexpected"):
            await call_openrouter("test prompt")

    @respx.mock
    async def test_empty_choices(self):
        respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=Response(200, json={"choices": []})
        )

        with pytest.raises(RuntimeError, match="Unexpected"):
            await call_openrouter("test prompt")

    @respx.mock
    async def test_request_payload_correct(self):
        mock_response = {
            "choices": [{"message": {"content": "OK"}}]
        }

        route = respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=Response(200, json=mock_response)
        )

        await call_openrouter("Hello LLM")

        assert route.called
        request = route.calls[0].request
        body = request.content.decode()

        assert "Hello LLM" in body
        assert "messages" in body

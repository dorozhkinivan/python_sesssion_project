import asyncio

from app.infra.celery_app import celery_app


@celery_app.task(name="llm_request", bind=True, max_retries=2)
def llm_request(self, tg_chat_id: int, prompt: str) -> str:
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_process_llm_request(tg_chat_id, prompt))
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)
    finally:
        loop.close()


async def _process_llm_request(tg_chat_id: int, prompt: str) -> str:
    from app.core.config import settings
    from app.services.openrouter_client import call_openrouter

    answer = await call_openrouter(prompt)

    await _send_telegram_message(tg_chat_id, answer, settings.TELEGRAM_BOT_TOKEN)

    return answer


async def _send_telegram_message(chat_id: int, text: str, bot_token: str) -> None:
    import httpx

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    if len(text) > 4000:
        text = text[:4000] + "..."

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                print(f"Telegram API error: {resp.status_code} {resp.text}")
    except httpx.HTTPError as e:
        print(f"Failed to send Telegram message: {e}")

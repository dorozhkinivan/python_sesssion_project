from aiogram import Router, types
from aiogram.filters import Command, CommandStart

from app.core.jwt import decode_and_validate
from app.infra.redis import get_redis
from app.tasks.llm_tasks import llm_request

router = Router()

TOKEN_PREFIX = "token:"


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет, я LLM консультант. Чтобы начать, авторизуйтесь:\n"
        "1. Зарегистрируйтесь в Auth Service: POST /auth/register\n"
        "2. Получите JWT токен: POST /auth/login\n"
        "3. Отправьте мне команду: /token <JWT>\n\n"
        "После этого пишите любые вопросы"
    )


@router.message(Command("token"))
async def cmd_token(message: types.Message):
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2 or not parts[1].strip():
        await message.answer("❌ Использование: /token <ваш_jwt_токен>")
        return

    token = parts[1].strip()

    try:
        payload = decode_and_validate(token)
    except ValueError as e:
        await message.answer(f"Невалидный токен: {e}")
        return

    redis = get_redis()
    key = f"{TOKEN_PREFIX}{message.from_user.id}"
    await redis.set(key, token)

    user_sub = payload.get("sub", "unknown")
    role = payload.get("role", "unknown")

    await message.answer(
        f"Токен принят и сохранён!\n"
        f"User ID: {user_sub}\n"
        f"Role: {role}\n\n"
        f"Можете задавать любые вопросы."
    )


@router.message()
async def handle_text(message: types.Message):
    if not message.text:
        await message.answer("Отправьте текстовое сообщение")
        return

    redis = get_redis()
    key = f"{TOKEN_PREFIX}{message.from_user.id}"
    token = await redis.get(key)

    if not token:
        await message.answer(
            "У вас нет сохранённого токена.\n\n"
            "Авторизуйтесь через Auth Service и отправьте:\n"
            "/token <JWT>"
        )
        return

    try:
        decode_and_validate(token)
    except ValueError:
        await redis.delete(key)
        await message.answer(
            "Ваш токен истёк или невалиден.\n\n"
            "Получите новый токен в Auth Service и отправьте:\n"
            "/token <JWT>"
        )
        return

    llm_request.delay(message.chat.id, message.text)

    await message.answer("Запрос принят! Ожидайте ответа от LLM следующим сообщением")

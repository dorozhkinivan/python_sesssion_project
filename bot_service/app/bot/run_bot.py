import asyncio
import logging

from app.bot.dispatcher import create_bot, create_dispatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    bot = create_bot()
    dp = create_dispatcher()

    logger.info("🤖 Bot is starting...")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()

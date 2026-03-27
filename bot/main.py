import logging

from aiogram import Bot, Dispatcher

from bot.config import settings
from bot.handlers.base import register_handlers
from bot.middlewares.logging import LoggingMiddleware


async def main() -> None:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.update.middleware(LoggingMiddleware())
    register_handlers(dp)
    await dp.start_polling(bot)

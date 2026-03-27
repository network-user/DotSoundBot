import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.core.logging import configure_logging
from bot.handlers import base, inline_mode
from bot.middlewares.logging import LoggingMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


async def main() -> None:
    configure_logging(settings.log_level)
    logger.info(
        "dotsound_bot_starting",
        log_level=settings.log_level,
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.update.outer_middleware(LoggingMiddleware())
    dp.message.middleware(ThrottlingMiddleware(rate_limit=0.7))

    dp.include_router(base.router)
    dp.include_router(inline_mode.router)

    logger.info("bot_polling_started")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        logger.info("bot_polling_stopped")
        await bot.session.close()

import asyncio

import structlog
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import MenuButtonWebApp, WebAppInfo

from bot.api.internal import create_internal_app
from bot.config import settings
from bot.core.logging import configure_logging
from bot.handlers import (
    audio,
    base,
    inline_mode,
    likes,
    playlists,
    stats,
    web_auth,
)
from bot.middlewares.logging import LoggingMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware

logger: structlog.stdlib.BoundLogger = structlog.get_logger(
    __name__
)


async def main() -> None:
    configure_logging(
        settings.log_level,
        redact=settings.redact_logs,
    )
    logger.info(
        "sound_bot_starting",
        log_level=settings.log_level,
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        ),
    )
    dp = Dispatcher()

    dp.update.outer_middleware(LoggingMiddleware())
    dp.message.middleware(
        ThrottlingMiddleware(rate_limit=0.7)
    )

    dp.include_router(web_auth.router)
    dp.include_router(likes.router)
    dp.include_router(audio.router)
    dp.include_router(stats.router)
    dp.include_router(playlists.router)
    dp.include_router(base.router)
    dp.include_router(inline_mode.router)

    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text=".Sound 🎵",
            web_app=WebAppInfo(
                url=settings.mini_app_url
            ),
        )
    )
    logger.info(
        "menu_button_set",
        mini_app_url=settings.mini_app_url,
    )

    internal_app = create_internal_app(bot)
    runner = web.AppRunner(internal_app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        "0.0.0.0",
        settings.internal_api_port,
    )
    await site.start()
    logger.info(
        "internal_api_started",
        port=settings.internal_api_port,
    )

    logger.info("bot_polling_started")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=(
                dp.resolve_used_update_types()
            ),
        )
    finally:
        logger.info("bot_polling_stopped")
        await runner.cleanup()
        await bot.session.close()

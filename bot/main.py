
import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.types import (
    CallbackQuery,
    ErrorEvent,
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)
from aiohttp import web

from bot.api.internal import create_internal_app
from bot.config import settings
from bot.core.logging import configure_logging
from bot.handlers import (
    artists,
    audio,
    base,
    inline_mode,
    likes,
    player,
    playlists,
    recommendations,
    stats,
    web_auth,
)
from bot.i18n.core import resolve_lang, tr
from bot.middlewares.logging import LoggingMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware

logger: structlog.stdlib.BoundLogger = structlog.get_logger(
    __name__
)


def _normalize_proxy_url(proxy_url: str) -> str:
    value = proxy_url.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1].strip()
    for marker in (" #", "\t#"):
        if marker in value:
            value = value.split(marker, 1)[0].strip()
    return value


def _split_proxy_urls(proxy_url: str) -> list[str]:
    return [
        normalized
        for candidate in proxy_url.split(",")
        if (normalized := _normalize_proxy_url(candidate))
    ]


def _create_telegram_session(
    proxy_url: str,
) -> AiohttpSession | None:
    candidates = _split_proxy_urls(proxy_url)
    if not candidates:
        return None
    for index, candidate in enumerate(candidates, start=1):
        try:
            session = AiohttpSession(proxy=candidate)
        except ValueError as exc:
            logger.error(
                "telegram_api_proxy_invalid",
                proxy_index=index,
                proxy_count=len(candidates),
                error_type=type(exc).__name__,
                detail=str(exc),
            )
            continue
        logger.info(
            "telegram_api_proxy_enabled",
            proxy_index=index,
            proxy_count=len(candidates),
        )
        return session
    return None



async def _global_error_handler(
    event: ErrorEvent,
) -> None:
    update = event.update
    logger.exception(
        "unhandled_handler_error",
        update_type=type(update).__name__,
        exception=type(event.exception).__name__,
    )
    target = (
        update.callback_query
        or update.inline_query
        or update.message
    )
    u = None
    if (
        update.callback_query
        and update.callback_query.from_user
    ):
        u = update.callback_query.from_user
    elif update.message and update.message.from_user:
        u = update.message.from_user
    elif (
        update.inline_query
        and update.inline_query.from_user
    ):
        u = update.inline_query.from_user
    ftext = tr(
        "app.fallback_error",
        resolve_lang(
            u.language_code if u else None
        ),
    )
    try:
        if isinstance(target, CallbackQuery):
            await target.answer(
                ftext, show_alert=True
            )
        elif isinstance(target, Message):
            await target.answer(ftext)
    except Exception:
        logger.debug("error_notify_failed")


async def main() -> None:
    configure_logging(
        settings.log_level,
        redact=settings.redact_logs,
        redact_identifiers=settings.redact_log_identifiers,
        json_output=not settings.debug,
        third_party_level=settings.log_third_party_level,
    )
    logger.info(
        "sound_bot_starting",
        log_level=settings.log_level,
    )

    session = _create_telegram_session(
        settings.telegram_api_proxy_url,
    )
    bot = Bot(
        token=settings.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.update.outer_middleware(LoggingMiddleware())
    throttle = ThrottlingMiddleware(
        rate_limit=settings.throttle_rate_limit,
        callback_rate_limit=(
            settings.throttle_callback_rate_limit
        ),
    )
    dp.message.middleware(throttle)
    dp.callback_query.middleware(throttle)
    dp.inline_query.middleware(throttle)
    dp.errors.register(_global_error_handler)

    dp.include_router(web_auth.router)
    dp.include_router(likes.router)
    dp.include_router(audio.router)
    dp.include_router(stats.router)
    dp.include_router(playlists.router)
    dp.include_router(player.router)
    dp.include_router(recommendations.router)
    dp.include_router(artists.router)
    dp.include_router(base.router)
    dp.include_router(inline_mode.router)

    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text=".sound",
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
        settings.internal_api_host,
        settings.internal_api_port,
    )
    await site.start()
    logger.info(
        "internal_api_started",
        host=settings.internal_api_host,
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

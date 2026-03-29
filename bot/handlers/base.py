import structlog
from aiogram import Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.api.client import BackendClient, BackendError
from bot.config import settings
from bot.keyboards.inline import (
    help_keyboard,
    main_keyboard,
    playlists_keyboard,
)

router = Router()
logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not message.from_user:
        return

    user = message.from_user
    structlog.contextvars.bind_contextvars(
        telegram_id=user.id,
        handler="cmd_start",
    )
    logger.info("cmd_start_called")

    async with BackendClient() as client:
        try:
            await client.post(
                "/api/v1/users",
                json={
                    "telegram_id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            )
            logger.info("user_registered_in_backend")
        except BackendError as exc:
            logger.error(
                "backend_registration_failed",
                status=exc.status_code,
                detail=exc.detail,
            )

    await message.answer(
        f"Привет, <b>{user.first_name}</b>! 👋\n\n"
        "Добро пожаловать в <b>DotSound</b> — музыка без рекламы.\n"
        "Слушай. Делись. Открывай.\n\n"
        "Загружай треки прямо в чат или открывай плеер:",
        reply_markup=main_keyboard(),
    )


@router.message(F.text == "/help")
async def cmd_help(message: Message) -> None:
    structlog.contextvars.bind_contextvars(handler="cmd_help")
    logger.info("cmd_help_called")
    await message.answer(
        "Что умеет DotSound:\n\n"
        "🎵 <b>Плеер</b> — слушай прямо в Telegram\n"
        "🔍 <b>Поиск</b> — введи название или исполнителя\n"
        "▤ <b>Плейлисты</b> — создавай свои подборки\n"
        "❤️ <b>Лайки</b> — сохраняй любимые треки\n"
        "👤 <b>Профиль</b> — статистика твоих загрузок\n"
        "📊 /mystats — статистика в чате",
        parse_mode="HTML",
        reply_markup=help_keyboard(),
    )


@router.message(F.text == "/profile")
async def cmd_profile(message: Message) -> None:
    if not message.from_user:
        return

    user = message.from_user
    structlog.contextvars.bind_contextvars(
        telegram_id=user.id, handler="cmd_profile"
    )
    logger.info("cmd_profile_called")

    async with BackendClient() as client:
        try:
            profile = await client.get_user_profile(user.id)
            stats = await client.get_user_stats(user.id)
            name = (
                profile.get("first_name") or ""
                + " "
                + (profile.get("last_name") or "")
            ).strip() or user.first_name
            username_str = (
                f"@{profile['username']}\n"
                if profile.get("username")
                else ""
            )
            await message.answer(
                f"👤 <b>{name}</b>\n"
                f"{username_str}"
                f"\n"
                f"🎵 Треков загружено: "
                f"<b>{stats.get('total_tracks', 0)}</b>\n"
                f"▶️ Прослушиваний: "
                f"<b>{stats.get('total_plays', 0)}</b>\n"
                f"❤️ Лайков: "
                f"<b>{stats.get('total_likes', 0)}</b>",
                parse_mode="HTML",
            )
        except BackendError as exc:
            logger.error(
                "profile_fetch_failed",
                status=exc.status_code,
                detail=exc.detail,
            )
            await message.answer(
                "Не удалось загрузить профиль. "
                "Попробуй позже."
            )


@router.message(F.text == "/playlists")
async def cmd_playlists(message: Message) -> None:
    if not message.from_user:
        return

    user = message.from_user
    structlog.contextvars.bind_contextvars(
        telegram_id=user.id, handler="cmd_playlists"
    )
    logger.info("cmd_playlists_called")

    async with BackendClient() as client:
        try:
            pls = await client.get_user_playlists(user.id)
            if not pls:
                await message.answer(
                    "У тебя пока нет плейлистов.\n"
                    "Открой плеер и создай первый! 🎵",
                    reply_markup=main_keyboard(),
                )
                return
            names = "\n".join(
                f"▤ <b>{pl['name']}</b>"
                for pl in pls[:10]
            )
            await message.answer(
                f"Твои плейлисты ({len(pls)}):\n\n{names}",
                parse_mode="HTML",
                reply_markup=playlists_keyboard(pls),
            )
        except BackendError as exc:
            logger.error(
                "playlists_fetch_failed",
                status=exc.status_code,
                detail=exc.detail,
            )
            await message.answer(
                "Не удалось загрузить плейлисты. "
                "Попробуй позже."
            )


@router.callback_query(F.data == "open_player")
async def on_open_player(callback: CallbackQuery) -> None:
    structlog.contextvars.bind_contextvars(
        handler="on_open_player",
        user_id=callback.from_user.id
        if callback.from_user
        else None,
    )
    logger.info("open_player_callback")
    await callback.answer()
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(
            reply_markup=main_keyboard()
        )


@router.callback_query(F.data == "profile")
async def on_profile_callback(callback: CallbackQuery) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    structlog.contextvars.bind_contextvars(
        handler="on_profile_callback",
        user_id=callback.from_user.id,
    )
    logger.info("profile_callback")
    await callback.answer(
        "Открой плеер → вкладка «Профиль»", show_alert=False
    )


@router.callback_query(F.data == "playlists")
async def on_playlists_callback(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    structlog.contextvars.bind_contextvars(
        handler="on_playlists_callback",
        user_id=callback.from_user.id,
    )
    logger.info("playlists_callback")
    async with BackendClient() as client:
        try:
            pls = await client.get_user_playlists(
                callback.from_user.id
            )
            if not pls:
                await callback.answer(
                    "Плейлистов пока нет", show_alert=True
                )
                return
            await callback.answer()
            if callback.message and isinstance(
                callback.message, Message
            ):
                names = "\n".join(
                    f"▤ {pl['name']}" for pl in pls[:5]
                )
                await callback.message.answer(
                    f"Твои плейлисты:\n{names}",
                    reply_markup=playlists_keyboard(pls),
                )
        except BackendError:
            await callback.answer(
                "Ошибка загрузки", show_alert=True
            )


@router.callback_query(F.data == "my_stats")
async def on_my_stats(callback: CallbackQuery) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    structlog.contextvars.bind_contextvars(
        handler="on_my_stats",
        user_id=callback.from_user.id,
    )
    await callback.answer()
    if callback.message and isinstance(callback.message, Message):
        await callback.message.answer(
            "📊 Используй /mystats для статистики"
        )


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(router)

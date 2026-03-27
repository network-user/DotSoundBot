import structlog
from aiogram import Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.api.client import BackendClient, BackendError
from bot.config import settings
from bot.keyboards.inline import help_keyboard, open_player_keyboard

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

    mini_app_url = f"{settings.backend_base_url}/mini_app/"
    await message.answer(
        f"Привет, {user.first_name}! 👋\n"
        "Добро пожаловать в DotSound — музыка без рекламы.",
        reply_markup=open_player_keyboard(mini_app_url),
    )


@router.message(F.text == "/help")
async def cmd_help(message: Message) -> None:
    structlog.contextvars.bind_contextvars(handler="cmd_help")
    logger.info("cmd_help_called")
    await message.answer(
        "Что умеет DotSound:\n\n"
        "🔍 <b>Поиск</b> — введи название или исполнителя\n"
        "🎵 <b>Плеер</b> — слушай прямо в Telegram\n"
        "❤️ <b>Лайки</b> — сохраняй любимые треки\n"
        "📋 <b>Плейлисты</b> — создавай свои подборки\n"
        "📊 /mystats — статистика твоих загрузок",
        parse_mode="HTML",
        reply_markup=help_keyboard(),
    )


@router.callback_query(F.data == "open_player")
async def on_open_player(callback: CallbackQuery) -> None:
    structlog.contextvars.bind_contextvars(
        handler="on_open_player",
        user_id=callback.from_user.id if callback.from_user else None,
    )
    logger.info("open_player_callback")
    mini_app_url = f"{settings.backend_base_url}/mini_app/"
    await callback.answer()
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(
            reply_markup=open_player_keyboard(mini_app_url)
        )


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(router)

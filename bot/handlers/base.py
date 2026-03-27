from aiogram import Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.config import settings
from bot.keyboards.inline import open_player_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 Привет! Я **DotSound** — твой проводник в мир музыки прямо "
        "в Telegram.\n\n"
        "🎵 Слушай любимые треки, находи новых исполнителей и делись "
        "своим творчеством. Без рекламы и подписок.\n\n"
        "Нажми кнопку ниже, чтобы открыть плеер! 👇",
        reply_markup=open_player_keyboard(settings.mini_app_url),
        parse_mode="Markdown",
    )


@router.message(F.text == "/help")
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📝 **Доступные команды:**\n\n"
        "/start — Главное меню и запуск плеера\n"
        "/help — Показать это сообщение\n\n"
        "DotSound — это UGC-платформа, где каждый может стать автором.",
        parse_mode="Markdown",
    )


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(router)

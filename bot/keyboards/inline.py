from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def open_player_keyboard(mini_app_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Открыть плеер",
            web_app={"url": mini_app_url},  # type: ignore[arg-type]
        )
    )
    return builder.as_markup()

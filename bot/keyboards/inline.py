from aiogram.types import (
    InlineKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def open_player_keyboard(mini_app_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎵 Открыть плеер",
        web_app=WebAppInfo(url=mini_app_url),
    )
    return builder.as_markup()


def help_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Поиск", switch_inline_query_current_chat="")
    builder.button(text="🎵 Плеер", callback_data="open_player")
    builder.adjust(2)
    return builder.as_markup()

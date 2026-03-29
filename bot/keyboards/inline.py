from aiogram.types import (
    InlineKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import settings


def open_player_keyboard(mini_app_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎵 Открыть .sound",
        web_app=WebAppInfo(url=mini_app_url),
    )
    return builder.as_markup()


def track_action_keyboard(
    track_id: int, mini_app_url: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❤️", callback_data=f"like_{track_id}"
    )
    builder.button(
        text="💔", callback_data=f"dislike_{track_id}"
    )
    builder.button(
        text="🎵 Слушать",
        web_app=WebAppInfo(url=mini_app_url),
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎵 Открыть плеер",
        web_app=WebAppInfo(url=settings.mini_app_url),
    )
    builder.button(text="👤 Профиль", callback_data="profile")
    builder.button(
        text="▤ Плейлисты", callback_data="playlists"
    )
    builder.adjust(1, 2)
    return builder.as_markup()


def help_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔍 Поиск", switch_inline_query_current_chat=""
    )
    builder.button(
        text="🎵 Плеер",
        web_app=WebAppInfo(url=settings.mini_app_url),
    )
    builder.button(
        text="📊 Моя статистика", callback_data="my_stats"
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def playlists_keyboard(
    playlists: list[dict],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pl in playlists[:10]:
        builder.button(
            text=f"▤ {pl['name']}",
            callback_data=f"playlist_{pl['id']}",
        )
    builder.button(
        text="＋ Создать плейлист",
        callback_data="create_playlist",
    )
    builder.adjust(1)
    return builder.as_markup()

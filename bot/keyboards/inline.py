from aiogram.types import (
    InlineKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
)

from bot.config import settings


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎵 Открыть плеер",
        web_app=WebAppInfo(url=settings.mini_app_url),
    )
    builder.button(
        text="🎧 Плеер",
        callback_data="menu:player",
    )
    builder.button(
        text="📅 Плейлист дня",
        callback_data="menu:daily_playlist",
    )
    builder.button(
        text="📆 Плейлист недели",
        callback_data="menu:weekly_playlist",
    )
    builder.button(
        text="👤 Профиль",
        callback_data="menu:profile",
    )
    builder.button(
        text="ℹ️ О проекте",
        callback_data="menu:about",
    )
    builder.button(
        text="🔐 История входов",
        callback_data="menu:login_history",
    )
    builder.adjust(1, 1, 2, 2, 1)
    return builder.as_markup()


def daily_playlist_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 Обновить (debug)",
        callback_data="rec:daily:refresh",
    )
    builder.button(
        text="← Назад в меню",
        callback_data="menu:main",
    )
    builder.adjust(1)
    return builder.as_markup()


def weekly_playlist_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="← Назад в меню",
        callback_data="menu:main",
    )
    return builder.as_markup()


def about_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎵 Возможности",
        callback_data="about:features",
    )
    builder.button(
        text="⚙️ Технологии",
        callback_data="about:tech",
    )
    builder.button(
        text="📤 Загрузка музыки",
        callback_data="about:upload",
    )
    builder.button(
        text="📥 Импорт из TG",
        callback_data="about:import",
    )
    builder.button(
        text="💻 Открытый код",
        callback_data="about:opensource",
    )
    builder.button(
        text="🚀 Планы",
        callback_data="about:roadmap",
    )
    builder.button(
        text="← Назад в меню",
        callback_data="menu:main",
    )
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def back_to_about_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="← Назад к разделам",
        callback_data="menu:about",
    )
    return builder.as_markup()


def profile_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎵 Открыть в плеере",
        web_app=WebAppInfo(url=settings.mini_app_url),
    )
    builder.button(
        text="← Назад в меню",
        callback_data="menu:main",
    )
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="← Назад в меню",
        callback_data="menu:main",
    )
    return builder.as_markup()


def open_player_keyboard(
    mini_app_url: str,
) -> InlineKeyboardMarkup:
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
        text="❤️",
        callback_data=f"like_{track_id}",
    )
    builder.button(
        text="💔",
        callback_data=f"dislike_{track_id}",
    )
    builder.button(
        text="🎵 Слушать",
        web_app=WebAppInfo(url=mini_app_url),
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


def player_source_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎵 Мои треки",
        callback_data="player:src:my",
    )
    builder.button(
        text="❤️ Лайки",
        callback_data="player:src:liked",
    )
    builder.button(
        text="📻 Лента",
        callback_data="player:src:feed",
    )
    builder.button(
        text="← Назад в меню",
        callback_data="menu:main",
    )
    builder.adjust(1)
    return builder.as_markup()


def player_control_kb(
    track_count: int,
    has_more: bool,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(track_count):
        builder.button(
            text=f"❤️ {i + 1}",
            callback_data=f"player:like:{i}",
        )
    if has_more:
        builder.button(
            text="Ещё 3 →",
            callback_data="player:next",
        )
    builder.button(
        text="← Главное меню",
        callback_data="player:menu",
    )
    like_row = list(range(track_count))
    rows: list[int] = [len(like_row)]
    if has_more:
        rows.append(1)
    rows.append(1)
    builder.adjust(*rows)
    return builder.as_markup()


def help_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔍 Поиск",
        switch_inline_query_current_chat="",
    )
    builder.button(
        text="🎵 Плеер",
        web_app=WebAppInfo(url=settings.mini_app_url),
    )
    builder.button(
        text="📊 Моя статистика",
        callback_data="my_stats",
    )
    builder.adjust(2, 1)
    return builder.as_markup()

from aiogram.types import (
    InlineKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
)

from bot.config import settings
from bot.i18n.core import tr


def main_menu_kb(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=tr("inline.main.open_app", lang),
        web_app=WebAppInfo(url=settings.mini_app_url),
    )
    builder.button(
        text=tr("inline.main.player", lang),
        callback_data="menu:player",
    )
    builder.button(
        text=tr("inline.main.profile", lang),
        callback_data="menu:profile",
    )
    builder.button(
        text=tr("inline.main.about", lang),
        callback_data="menu:about",
    )
    builder.button(
        text=tr("inline.main.login_history", lang),
        callback_data="menu:login_history",
    )
    builder.adjust(1, 1, 2, 1)
    return builder.as_markup()


def about_kb(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=tr("inline.about.features", lang),
        callback_data="about:features",
    )
    builder.button(
        text=tr("inline.about.tech", lang),
        callback_data="about:tech",
    )
    builder.button(
        text=tr("inline.about.upload", lang),
        callback_data="about:upload",
    )
    builder.button(
        text=tr("inline.about.import", lang),
        callback_data="about:import",
    )
    builder.button(
        text=tr("inline.about.opensource", lang),
        callback_data="about:opensource",
    )
    builder.button(
        text=tr("inline.about.roadmap", lang),
        callback_data="about:roadmap",
    )
    builder.button(
        text=tr("inline.back.menu", lang),
        callback_data="menu:main",
    )
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def back_to_about_kb(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=tr("inline.back.about", lang),
        callback_data="menu:about",
    )
    return builder.as_markup()


def profile_kb(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=tr("inline.profile.open", lang),
        web_app=WebAppInfo(url=settings.mini_app_url),
    )
    builder.button(
        text=tr("inline.back.menu", lang),
        callback_data="menu:main",
    )
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_kb(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=tr("inline.back.menu", lang),
        callback_data="menu:main",
    )
    return builder.as_markup()


def open_player_keyboard(
    mini_app_url: str,
    lang: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=tr("inline.open_sound", lang),
        web_app=WebAppInfo(url=mini_app_url),
    )
    return builder.as_markup()


def track_action_keyboard(
    track_id: int, mini_app_url: str, lang: str
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
        text=tr("inline.listen", lang),
        web_app=WebAppInfo(url=mini_app_url),
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def playlists_keyboard(
    playlists: list[dict], lang: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pl in playlists[:10]:
        builder.button(
            text=f"▤ {pl['name']}",
            callback_data=f"playlist_{pl['id']}",
        )
    builder.button(
        text=tr("inline.create_playlist", lang),
        callback_data="create_playlist",
    )
    builder.adjust(1)
    return builder.as_markup()


def player_source_kb(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=tr("inline.player.my", lang),
        callback_data="player:src:my",
    )
    builder.button(
        text=tr("inline.player.liked", lang),
        callback_data="player:src:liked",
    )
    builder.button(
        text=tr("inline.player.feed", lang),
        callback_data="player:src:feed",
    )
    builder.button(
        text=tr("inline.player.follows", lang),
        callback_data="player:src:follows",
    )
    builder.button(
        text=tr("inline.player.playlists", lang),
        callback_data="player:src:playlists",
    )
    builder.button(
        text=tr("inline.player.recommendations", lang),
        callback_data="player:src:recommendations",
    )
    builder.button(
        text=tr("inline.back.menu", lang),
        callback_data="menu:main",
    )
    builder.adjust(1)
    return builder.as_markup()


def player_control_kb(
    track_count: int,
    has_more: bool,
    lang: str,
    shuffle_enabled: bool = False,
    can_go_back: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(track_count):
        builder.button(
            text=f"❤️ {i + 1}",
            callback_data=f"player:like:{i}",
        )
    if has_more:
        builder.button(
            text=tr("inline.player.more3", lang),
            callback_data="player:next",
        )
    if can_go_back:
        builder.button(
            text=tr("inline.player.prev3", lang),
            callback_data="player:prev",
        )
    builder.button(
        text=tr(
            "inline.player.shuffle_on",
            lang,
        )
        if shuffle_enabled
        else tr("inline.player.shuffle_off", lang),
        callback_data="player:shuffle",
    )
    builder.button(
        text=tr("inline.player.back_main", lang),
        callback_data="player:menu",
    )
    like_row = list(range(track_count))
    rows: list[int] = [len(like_row)]
    if has_more:
        rows.append(1)
    if can_go_back:
        rows.append(1)
    rows.append(1)
    rows.append(1)
    builder.adjust(*rows)
    return builder.as_markup()


def help_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=tr("inline.help.search", lang),
        switch_inline_query_current_chat="",
    )
    builder.button(
        text=tr("inline.main.player", lang),
        web_app=WebAppInfo(url=settings.mini_app_url),
    )
    builder.button(
        text=tr("inline.help.stats", lang),
        callback_data="my_stats",
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def daily_playlist_kb(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=tr("recs.refresh", lang),
        callback_data="rec:daily:refresh",
    )
    builder.button(
        text=tr("recs.daily_back", lang),
        callback_data="menu:main",
    )
    builder.adjust(1, 1)
    return builder.as_markup()


def weekly_playlist_kb(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=tr("recs.weekly_back", lang),
        callback_data="menu:main",
    )
    return builder.as_markup()

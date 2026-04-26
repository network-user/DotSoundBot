from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest
from aiogram.types import Message

from bot.api.client import BackendError

pytestmark = pytest.mark.anyio


def _make_message(user_id: int = 1) -> MagicMock:
    msg = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.first_name = "Alice"
    msg.from_user.username = "alice"
    msg.from_user.last_name = None
    msg.from_user.language_code = "ru"
    msg.answer = AsyncMock()
    return msg


def _make_callback(
    data: str, user_id: int = 1
) -> MagicMock:
    cb = AsyncMock()
    cb.from_user = MagicMock()
    cb.from_user.id = user_id
    cb.from_user.first_name = "Alice"
    cb.from_user.language_code = "ru"
    cb.data = data
    cb.answer = AsyncMock()
    cb.message = AsyncMock(spec=Message)
    cb.message.edit_text = AsyncMock()
    return cb


def _backend_ctx(client: AsyncMock) -> MagicMock:
    cls = MagicMock()
    cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )
    return cls


# ------------------------------------------------------------------
# cmd_start
# ------------------------------------------------------------------


@patch("bot.handlers.base.BackendClient")
async def test_cmd_start_sends_welcome(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.base import cmd_start

    client = AsyncMock()
    client.post = AsyncMock(return_value={"id": 1})
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message()

    await cmd_start(msg)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "Alice" in text
    assert ".sound" in text


@patch("bot.handlers.base.BackendClient")
async def test_cmd_start_backend_failure(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.base import cmd_start

    client = AsyncMock()
    client.post = AsyncMock(
        side_effect=Exception("conn")
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message()

    await cmd_start(msg)

    msg.answer.assert_awaited_once()


async def test_cmd_start_no_user() -> None:
    from bot.handlers.base import cmd_start

    msg = AsyncMock()
    msg.from_user = None
    msg.answer = AsyncMock()

    await cmd_start(msg)

    msg.answer.assert_not_awaited()


# ------------------------------------------------------------------
# on_main_menu
# ------------------------------------------------------------------


async def test_on_main_menu() -> None:
    from bot.handlers.base import on_main_menu

    cb = _make_callback("menu:main")

    await on_main_menu(cb)

    cb.answer.assert_awaited_once()
    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "Alice" in text


async def test_on_main_menu_no_user() -> None:
    from bot.handlers.base import on_main_menu

    cb = _make_callback("menu:main")
    cb.from_user = None

    await on_main_menu(cb)

    cb.answer.assert_awaited_once()
    cb.message.edit_text.assert_not_awaited()


# ------------------------------------------------------------------
# on_about
# ------------------------------------------------------------------


async def test_on_about_shows_menu() -> None:
    from bot.handlers.base import on_about

    cb = _make_callback("menu:about")

    await on_about(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert ".sound" in text


# ------------------------------------------------------------------
# on_about_section
# ------------------------------------------------------------------


async def test_on_about_section_valid() -> None:
    from bot.handlers.base import on_about_section

    cb = _make_callback("about:features")

    await on_about_section(cb)

    cb.answer.assert_awaited()
    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "Возможности" in text


async def test_on_about_section_tech() -> None:
    from bot.handlers.base import on_about_section

    cb = _make_callback("about:tech")

    await on_about_section(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "Технологии" in text


async def test_on_about_section_upload() -> None:
    from bot.handlers.base import on_about_section

    cb = _make_callback("about:upload")

    await on_about_section(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "загрузить" in text.lower()


async def test_on_about_section_import() -> None:
    from bot.handlers.base import on_about_section

    cb = _make_callback("about:import")

    await on_about_section(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "Импорт" in text


async def test_on_about_section_opensource() -> None:
    from bot.handlers.base import on_about_section

    cb = _make_callback("about:opensource")

    await on_about_section(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "open source" in text.lower()


async def test_on_about_section_roadmap() -> None:
    from bot.handlers.base import on_about_section

    cb = _make_callback("about:roadmap")

    await on_about_section(cb)

    cb.message.edit_text.assert_awaited_once()


async def test_on_about_section_invalid() -> None:
    from bot.handlers.base import on_about_section

    cb = _make_callback("about:nonexistent")

    await on_about_section(cb)

    cb.answer.assert_awaited_once()
    text = cb.answer.call_args[0][0]
    assert "не найден" in text.lower()


async def test_on_about_section_no_data() -> None:
    from bot.handlers.base import on_about_section

    cb = _make_callback("about:features")
    cb.data = None

    await on_about_section(cb)

    cb.answer.assert_awaited_once()


# ------------------------------------------------------------------
# on_profile
# ------------------------------------------------------------------


@patch("bot.handlers.base.BackendClient")
async def test_on_profile_success(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.base import on_profile

    client = AsyncMock()
    client.get_user_profile = AsyncMock(
        return_value={
            "id": 5,
            "first_name": "Alice",
            "last_name": "",
            "username": "alice",
        }
    )
    client.get_user_stats = AsyncMock(
        return_value={
            "total_tracks": 10,
            "total_plays": 50,
            "total_likes": 3,
            "followers_count": 2,
        }
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    cb = _make_callback("menu:profile")

    await on_profile(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "Alice" in text
    assert "10" in text


@patch("bot.handlers.base.BackendClient")
async def test_on_profile_backend_error(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.base import on_profile

    client = AsyncMock()
    client.get_user_profile = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    cb = _make_callback("menu:profile")

    await on_profile(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "Не удалось" in text


async def test_on_profile_no_user() -> None:
    from bot.handlers.base import on_profile

    cb = _make_callback("menu:profile")
    cb.from_user = None

    await on_profile(cb)

    cb.answer.assert_awaited_once()


@patch("bot.handlers.base.BackendClient")
async def test_on_profile_with_username(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.base import on_profile

    client = AsyncMock()
    client.get_user_profile = AsyncMock(
        return_value={
            "id": 5,
            "first_name": "Bob",
            "last_name": "Smith",
            "username": "bobsmith",
        }
    )
    client.get_user_stats = AsyncMock(
        return_value={
            "total_tracks": 0,
            "total_plays": 0,
            "total_likes": 0,
            "followers_count": 0,
        }
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    cb = _make_callback("menu:profile")

    await on_profile(cb)

    text = cb.message.edit_text.call_args[0][0]
    assert "@bobsmith" in text
    assert "Bob Smith" in text


# ------------------------------------------------------------------
# on_login_history
# ------------------------------------------------------------------


@patch("bot.handlers.base.BackendClient")
async def test_on_login_history_empty(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.base import on_login_history

    client = AsyncMock()
    client.get_user_profile = AsyncMock(
        return_value={"id": 5}
    )
    client.get_login_history = AsyncMock(
        return_value=[]
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    cb = _make_callback("menu:login_history")

    await on_login_history(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "Нет записей" in text


@patch("bot.handlers.base.BackendClient")
async def test_on_login_history_with_entries(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.base import on_login_history

    client = AsyncMock()
    client.get_user_profile = AsyncMock(
        return_value={"id": 5}
    )
    client.get_login_history = AsyncMock(
        return_value=[
            {
                "created_at": "2025-01-01T12:00:00",
                "device": "Chrome",
                "ip": "1.2.3.4",
            }
        ]
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    cb = _make_callback("menu:login_history")

    await on_login_history(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "Chrome" in text
    assert "1.2.3.4" in text


@patch("bot.handlers.base.BackendClient")
async def test_on_login_history_backend_error(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.base import on_login_history

    client = AsyncMock()
    client.get_user_profile = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    cb = _make_callback("menu:login_history")

    await on_login_history(cb)

    text = cb.message.edit_text.call_args[0][0]
    assert "Не удалось" in text


async def test_on_login_history_no_user() -> None:
    from bot.handlers.base import on_login_history

    cb = _make_callback("menu:login_history")
    cb.from_user = None

    await on_login_history(cb)

    cb.answer.assert_awaited_once()


# ------------------------------------------------------------------
# cmd_help
# ------------------------------------------------------------------


async def test_cmd_help_sends_help_text() -> None:
    from bot.handlers.base import cmd_help

    msg = _make_message()

    await cmd_help(msg)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "Плеер" in text
    assert "Поиск" in text


# ------------------------------------------------------------------
# cmd_profile
# ------------------------------------------------------------------


@patch("bot.handlers.base.BackendClient")
async def test_cmd_profile_success(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.base import cmd_profile

    client = AsyncMock()
    client.get_user_profile = AsyncMock(
        return_value={
            "id": 5,
            "first_name": "Alice",
            "last_name": None,
        }
    )
    client.get_user_stats = AsyncMock(
        return_value={
            "total_tracks": 3,
            "total_plays": 10,
            "total_likes": 1,
        }
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message()

    await cmd_profile(msg)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "Alice" in text
    assert "3" in text


@patch("bot.handlers.base.BackendClient")
async def test_cmd_profile_backend_error(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.base import cmd_profile

    client = AsyncMock()
    client.get_user_profile = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message()

    await cmd_profile(msg)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "Не удалось" in text


async def test_cmd_profile_no_user() -> None:
    from bot.handlers.base import cmd_profile

    msg = AsyncMock()
    msg.from_user = None
    msg.answer = AsyncMock()

    await cmd_profile(msg)

    msg.answer.assert_not_awaited()


# ------------------------------------------------------------------
# cmd_playlists
# ------------------------------------------------------------------


@patch("bot.handlers.base.BackendClient")
async def test_cmd_playlists_empty(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.base import cmd_playlists

    client = AsyncMock()
    client.get_user_playlists = AsyncMock(
        return_value=[]
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message()

    await cmd_playlists(msg)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "нет плейлистов" in text.lower()


@patch("bot.handlers.base.BackendClient")
async def test_cmd_playlists_with_items(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.base import cmd_playlists

    client = AsyncMock()
    client.get_user_playlists = AsyncMock(
        return_value=[
            {"id": 1, "name": "Chill"},
            {"id": 2, "name": "Workout"},
        ]
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message()

    await cmd_playlists(msg)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "Chill" in text
    assert "Workout" in text
    assert "(2)" in text


@patch("bot.handlers.base.BackendClient")
async def test_cmd_playlists_backend_error(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.base import cmd_playlists

    client = AsyncMock()
    client.get_user_playlists = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message()

    await cmd_playlists(msg)

    text = msg.answer.call_args[0][0]
    assert "Не удалось" in text


async def test_cmd_playlists_no_user() -> None:
    from bot.handlers.base import cmd_playlists

    msg = AsyncMock()
    msg.from_user = None
    msg.answer = AsyncMock()

    await cmd_playlists(msg)

    msg.answer.assert_not_awaited()


# ------------------------------------------------------------------
# _main_menu_text
# ------------------------------------------------------------------


def test_main_menu_welcome() -> None:
    from bot.utils.formatting import (
        format_main_menu_welcome,
    )

    text = format_main_menu_welcome("Bob", "ru")

    assert "Bob" in text
    assert ".sound" in text

from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest
from aiogram.types import Message

from bot.api.client import BackendError

pytestmark = pytest.mark.anyio


def _make_callback(
    data: str, user_id: int = 1
) -> MagicMock:
    cb = AsyncMock()
    cb.from_user = MagicMock()
    cb.from_user.id = user_id
    cb.from_user.language_code = "ru"
    cb.data = data
    cb.answer = AsyncMock()
    cb.message = AsyncMock(spec=Message)
    cb.message.answer = AsyncMock()
    return cb


def _make_message(
    text: str = "", user_id: int = 1
) -> MagicMock:
    msg = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.language_code = "ru"
    msg.text = text
    msg.answer = AsyncMock()
    return msg


# ------------------------------------------------------------------
# on_create_playlist
# ------------------------------------------------------------------


async def test_on_create_playlist_sets_state(
) -> None:
    from bot.handlers.playlists import (
        on_create_playlist,
    )

    cb = _make_callback("create_playlist")
    state = AsyncMock()
    state.set_state = AsyncMock()

    await on_create_playlist(cb, state)

    cb.answer.assert_awaited_once()
    state.set_state.assert_awaited_once()


async def test_on_create_playlist_no_user() -> None:
    from bot.handlers.playlists import (
        on_create_playlist,
    )

    cb = _make_callback("create_playlist")
    cb.from_user = None
    state = AsyncMock()

    await on_create_playlist(cb, state)

    cb.answer.assert_awaited_once()
    state.set_state.assert_not_awaited()


# ------------------------------------------------------------------
# on_playlist_name_received
# ------------------------------------------------------------------


@patch("bot.handlers.playlists.BackendClient")
async def test_on_playlist_name_received_success(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.playlists import (
        on_playlist_name_received,
    )

    client = AsyncMock()
    client.create_playlist = AsyncMock(
        return_value={"id": 1, "name": "Chill"}
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message("Chill")
    state = AsyncMock()
    state.clear = AsyncMock()

    await on_playlist_name_received(msg, state)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "Chill" in text
    state.clear.assert_awaited_once()


@patch("bot.handlers.playlists.BackendClient")
async def test_on_playlist_name_received_error(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.playlists import (
        on_playlist_name_received,
    )

    client = AsyncMock()
    client.create_playlist = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message("BadList")
    state = AsyncMock()
    state.clear = AsyncMock()

    await on_playlist_name_received(msg, state)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "Не удалось" in text


async def test_on_playlist_name_empty() -> None:
    from bot.handlers.playlists import (
        on_playlist_name_received,
    )

    msg = _make_message("   ")
    state = AsyncMock()

    await on_playlist_name_received(msg, state)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "пустым" in text.lower() or "Название" in text


async def test_on_playlist_name_no_user() -> None:
    from bot.handlers.playlists import (
        on_playlist_name_received,
    )

    msg = AsyncMock()
    msg.from_user = None
    msg.text = "Test"
    msg.answer = AsyncMock()
    state = AsyncMock()

    await on_playlist_name_received(msg, state)

    msg.answer.assert_not_awaited()


async def test_on_playlist_name_no_text() -> None:
    from bot.handlers.playlists import (
        on_playlist_name_received,
    )

    msg = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = 1
    msg.from_user.language_code = "ru"
    msg.text = None
    msg.answer = AsyncMock()
    state = AsyncMock()

    await on_playlist_name_received(msg, state)

    msg.answer.assert_not_awaited()


async def test_on_playlist_name_slash_command(
) -> None:
    from bot.handlers.playlists import (
        on_playlist_name_received,
    )

    msg = _make_message("/cancel")
    state = AsyncMock()
    state.clear = AsyncMock()

    await on_playlist_name_received(msg, state)

    state.clear.assert_awaited_once()
    msg.answer.assert_not_awaited()


# ------------------------------------------------------------------
# on_playlist_selected
# ------------------------------------------------------------------


@patch("bot.handlers.playlists.BackendClient")
async def test_on_playlist_selected_success(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.playlists import (
        on_playlist_selected,
    )

    client = AsyncMock()
    client.get_playlist_detail = AsyncMock(
        return_value={
            "name": "Chill",
            "tracks": [
                {"title": "Song A"},
                {"title": "Song B"},
            ],
        }
    )
    client.get_user_playlists = AsyncMock(
        return_value=[{"id": 1, "name": "Chill"}]
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    cb = _make_callback("playlist_1")

    await on_playlist_selected(cb)

    cb.answer.assert_awaited()
    cb.message.answer.assert_awaited_once()
    text = cb.message.answer.call_args[0][0]
    assert "Chill" in text
    assert "Song A" in text


@patch("bot.handlers.playlists.BackendClient")
async def test_on_playlist_selected_empty_tracks(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.playlists import (
        on_playlist_selected,
    )

    client = AsyncMock()
    client.get_playlist_detail = AsyncMock(
        return_value={
            "name": "Empty",
            "tracks": [],
        }
    )
    client.get_user_playlists = AsyncMock(
        return_value=[{"id": 2, "name": "Empty"}]
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    cb = _make_callback("playlist_2")

    await on_playlist_selected(cb)

    text = cb.message.answer.call_args[0][0]
    assert "Треков пока нет" in text


@patch("bot.handlers.playlists.BackendClient")
async def test_on_playlist_selected_backend_error(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.playlists import (
        on_playlist_selected,
    )

    client = AsyncMock()
    client.get_playlist_detail = AsyncMock(
        side_effect=BackendError(404, "nope")
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    cb = _make_callback("playlist_999")

    await on_playlist_selected(cb)

    cb.answer.assert_awaited()
    text = cb.answer.call_args[0][0]
    assert "Не удалось" in text


async def test_on_playlist_selected_no_user(
) -> None:
    from bot.handlers.playlists import (
        on_playlist_selected,
    )

    cb = _make_callback("playlist_1")
    cb.from_user = None

    await on_playlist_selected(cb)

    cb.answer.assert_awaited_once()


async def test_on_playlist_selected_invalid_id(
) -> None:
    from bot.handlers.playlists import (
        on_playlist_selected,
    )

    cb = _make_callback("playlist_abc")

    await on_playlist_selected(cb)

    cb.answer.assert_awaited_once()

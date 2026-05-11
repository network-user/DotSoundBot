from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest
from aiogram.types import Message

from bot.api.client import BackendError

pytestmark = pytest.mark.anyio


def _make_callback(data: str, user_id: int = 1) -> MagicMock:
    cb = AsyncMock()
    cb.from_user = MagicMock()
    cb.from_user.id = user_id
    cb.from_user.language_code = "ru"
    cb.data = data
    cb.answer = AsyncMock()
    cb.message = AsyncMock(spec=Message)
    cb.message.edit_text = AsyncMock()
    return cb


def _patched_backend(client: AsyncMock) -> MagicMock:
    cm = MagicMock()
    cm.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    cm.return_value.__aexit__ = AsyncMock(
        return_value=False
    )
    return cm


# ------------------------------------------------------------------
# _fmt_track / _fmt_external
# ------------------------------------------------------------------


def test_fmt_track_escapes_html() -> None:
    from bot.handlers.recommendations import _fmt_track

    out = _fmt_track(
        {"title": "<b>hi</b>", "artist_name": "A&B"}
    )
    assert "&lt;b&gt;hi&lt;/b&gt;" in out
    assert "A&amp;B" in out


def test_fmt_track_artist_fallback() -> None:
    from bot.handlers.recommendations import _fmt_track

    out = _fmt_track(
        {"title": "Song", "artist": "Fallback"}
    )
    assert "Fallback" in out


def test_fmt_track_no_artist() -> None:
    from bot.handlers.recommendations import _fmt_track

    out = _fmt_track({"title": "Song"})
    assert "<b>Song</b>" == out


def test_fmt_external_escapes_html() -> None:
    from bot.handlers.recommendations import _fmt_external

    out = _fmt_external(
        {"title": "T<i>", "artist": "X>"}
    )
    assert "&lt;" in out
    assert "&gt;" in out


def test_fmt_external_no_artist() -> None:
    from bot.handlers.recommendations import _fmt_external

    out = _fmt_external({"title": "OnlyTitle"})
    assert out == "<b>OnlyTitle</b>"


# ------------------------------------------------------------------
# on_daily_playlist
# ------------------------------------------------------------------


@patch("bot.handlers.recommendations.BackendClient")
async def test_on_daily_playlist_success(
    mock_cls: MagicMock,
) -> None:
    from bot.handlers.recommendations import (
        on_daily_playlist,
    )

    client = AsyncMock()
    client.get_daily_playlist = AsyncMock(
        return_value={
            "internal_tracks": [
                {"title": "I1", "artist_name": "A1"}
            ],
            "external_suggestions": [
                {"title": "E1", "artist": "EA"}
            ],
            "global_top": [
                {"title": "G1", "artist_name": "GA"}
            ],
        }
    )
    mock_cls.side_effect = lambda: _patched_backend(
        client
    ).return_value

    cb = _make_callback("menu:daily_playlist")
    await on_daily_playlist(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "I1" in text
    assert "E1" in text
    assert "G1" in text


@patch("bot.handlers.recommendations.BackendClient")
async def test_on_daily_playlist_empty_internal(
    mock_cls: MagicMock,
) -> None:
    from bot.handlers.recommendations import (
        on_daily_playlist,
    )

    client = AsyncMock()
    client.get_daily_playlist = AsyncMock(
        return_value={
            "internal_tracks": [],
            "external_suggestions": [],
            "global_top": [],
        }
    )
    mock_cls.side_effect = lambda: _patched_backend(
        client
    ).return_value

    cb = _make_callback("menu:daily_playlist")
    await on_daily_playlist(cb)

    cb.message.edit_text.assert_awaited_once()


@patch("bot.handlers.recommendations.BackendClient")
async def test_on_daily_playlist_backend_error(
    mock_cls: MagicMock,
) -> None:
    from bot.handlers.recommendations import (
        on_daily_playlist,
    )

    client = AsyncMock()
    client.get_daily_playlist = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_cls.side_effect = lambda: _patched_backend(
        client
    ).return_value

    cb = _make_callback("menu:daily_playlist")
    await on_daily_playlist(cb)

    cb.message.edit_text.assert_awaited_once()


async def test_on_daily_playlist_no_user() -> None:
    from bot.handlers.recommendations import (
        on_daily_playlist,
    )

    cb = _make_callback("menu:daily_playlist")
    cb.from_user = None

    await on_daily_playlist(cb)

    cb.answer.assert_awaited_once()


# ------------------------------------------------------------------
# on_weekly_playlist
# ------------------------------------------------------------------


@patch("bot.handlers.recommendations.BackendClient")
async def test_on_weekly_playlist_success(
    mock_cls: MagicMock,
) -> None:
    from bot.handlers.recommendations import (
        on_weekly_playlist,
    )

    client = AsyncMock()
    client.get_weekly_playlist = AsyncMock(
        return_value={
            "internal_tracks": [
                {"title": "Weekly1", "artist": "WA"}
            ],
            "external_suggestions": [
                {"title": "Ext1"}
            ],
        }
    )
    mock_cls.side_effect = lambda: _patched_backend(
        client
    ).return_value

    cb = _make_callback("menu:weekly_playlist")
    await on_weekly_playlist(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "Weekly1" in text
    assert "Ext1" in text


@patch("bot.handlers.recommendations.BackendClient")
async def test_on_weekly_playlist_backend_error(
    mock_cls: MagicMock,
) -> None:
    from bot.handlers.recommendations import (
        on_weekly_playlist,
    )

    client = AsyncMock()
    client.get_weekly_playlist = AsyncMock(
        side_effect=BackendError(503, "down")
    )
    mock_cls.side_effect = lambda: _patched_backend(
        client
    ).return_value

    cb = _make_callback("menu:weekly_playlist")
    await on_weekly_playlist(cb)

    cb.message.edit_text.assert_awaited_once()


async def test_on_weekly_playlist_no_user() -> None:
    from bot.handlers.recommendations import (
        on_weekly_playlist,
    )

    cb = _make_callback("menu:weekly_playlist")
    cb.from_user = None

    await on_weekly_playlist(cb)

    cb.answer.assert_awaited_once()


# ------------------------------------------------------------------
# on_refresh_daily
# ------------------------------------------------------------------


@patch("bot.handlers.recommendations.BackendClient")
async def test_on_refresh_daily_success(
    mock_cls: MagicMock,
) -> None:
    from bot.handlers.recommendations import (
        on_refresh_daily,
    )

    client = AsyncMock()
    client.refresh_daily_playlist = AsyncMock(
        return_value=None
    )
    mock_cls.side_effect = lambda: _patched_backend(
        client
    ).return_value

    cb = _make_callback("rec:daily:refresh")
    await on_refresh_daily(cb)

    cb.answer.assert_awaited()
    client.refresh_daily_playlist.assert_awaited_once_with(
        1
    )


@patch("bot.handlers.recommendations.BackendClient")
async def test_on_refresh_daily_admin_only(
    mock_cls: MagicMock,
) -> None:
    from bot.handlers.recommendations import (
        on_refresh_daily,
    )

    client = AsyncMock()
    client.refresh_daily_playlist = AsyncMock(
        side_effect=BackendError(403, "forbidden")
    )
    mock_cls.side_effect = lambda: _patched_backend(
        client
    ).return_value

    cb = _make_callback("rec:daily:refresh")
    await on_refresh_daily(cb)

    cb.answer.assert_awaited()


@patch("bot.handlers.recommendations.BackendClient")
async def test_on_refresh_daily_other_error(
    mock_cls: MagicMock,
) -> None:
    from bot.handlers.recommendations import (
        on_refresh_daily,
    )

    client = AsyncMock()
    client.refresh_daily_playlist = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_cls.side_effect = lambda: _patched_backend(
        client
    ).return_value

    cb = _make_callback("rec:daily:refresh")
    await on_refresh_daily(cb)

    cb.answer.assert_awaited()


async def test_on_refresh_daily_no_user() -> None:
    from bot.handlers.recommendations import (
        on_refresh_daily,
    )

    cb = _make_callback("rec:daily:refresh")
    cb.from_user = None

    await on_refresh_daily(cb)

    cb.answer.assert_awaited_once()

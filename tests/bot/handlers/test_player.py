from __future__ import annotations

import time
from typing import Any
from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest
from aiogram.types import Message

from bot.api.client import BackendError
from bot.services.player_session import (
    PlayerSession,
    PlayerSessionManager,
)

pytestmark = pytest.mark.anyio


def _make_callback(
    data: str, user_id: int = 1
) -> MagicMock:
    cb = AsyncMock()
    cb.from_user = MagicMock()
    cb.from_user.id = user_id
    cb.from_user.first_name = "Alice"
    cb.data = data
    cb.answer = AsyncMock()
    cb.message = AsyncMock(spec=Message)
    cb.message.chat = MagicMock()
    cb.message.chat.id = 100
    cb.message.edit_text = AsyncMock()
    cb.message.delete = AsyncMock()
    cb.bot = AsyncMock()
    cb.bot.send_message = AsyncMock()
    cb.bot.send_audio = AsyncMock()
    cb.bot.delete_message = AsyncMock()
    cb.bot.edit_message_text = AsyncMock()
    cb.bot.edit_message_media = AsyncMock()
    return cb


def _tracks(n: int = 3) -> list[dict[str, Any]]:
    return [
        {
            "id": i,
            "title": f"Track {i}",
            "artist": f"Artist {i}",
            "source": "soundcloud",
        }
        for i in range(1, n + 1)
    ]


def _audio_msg(
    message_id: int = 1,
) -> MagicMock:
    msg = MagicMock()
    msg.message_id = message_id
    msg.audio = MagicMock()
    msg.audio.file_id = f"fid_{message_id}"
    return msg


# ------------------------------------------------------------------
# _get_token
# ------------------------------------------------------------------


@patch("bot.handlers.player.settings")
@patch("bot.handlers.player.BackendClient")
async def test_get_token_cached(
    mock_cls: MagicMock,
    mock_settings: MagicMock,
) -> None:
    from bot.handlers.player import (
        _get_token,
        _token_cache,
    )

    _token_cache[99] = ("tok", 5, time.time())
    client = AsyncMock()
    try:
        token, uid = await _get_token(client, 99)
        assert token == "tok"
        assert uid == 5
        client.get_internal_token.assert_not_awaited()
    finally:
        _token_cache.pop(99, None)


@patch("bot.handlers.player.settings")
async def test_get_token_fetches_when_missing(
    mock_settings: MagicMock,
) -> None:
    from bot.handlers.player import (
        _get_token,
        _token_cache,
    )

    mock_settings.internal_api_secret = "sec"
    client = AsyncMock()
    client.get_internal_token = AsyncMock(
        return_value={
            "access_token": "new_tok",
            "user_id": 7,
        }
    )
    _token_cache.pop(77, None)
    try:
        token, uid = await _get_token(client, 77)
        assert token == "new_tok"
        assert uid == 7
        assert 77 in _token_cache
    finally:
        _token_cache.pop(77, None)


@patch("bot.handlers.player.settings")
async def test_get_token_expired_cache(
    mock_settings: MagicMock,
) -> None:
    from bot.handlers.player import (
        _get_token,
        _token_cache,
    )

    mock_settings.internal_api_secret = "sec"
    _token_cache[88] = ("old", 1, time.time() - 9999)
    client = AsyncMock()
    client.get_internal_token = AsyncMock(
        return_value={
            "access_token": "fresh",
            "user_id": 2,
        }
    )
    try:
        token, uid = await _get_token(client, 88)
        assert token == "fresh"
        assert uid == 2
    finally:
        _token_cache.pop(88, None)


# ------------------------------------------------------------------
# _fetch_playable_tracks
# ------------------------------------------------------------------


async def test_fetch_playable_tracks_my() -> None:
    from bot.handlers.player import (
        _fetch_playable_tracks,
    )

    client = AsyncMock()
    client.get_my_tracks = AsyncMock(
        return_value={
            "items": _tracks(3),
            "total": 10,
        }
    )

    items, total, has_more = (
        await _fetch_playable_tracks(
            client, "my", "tok", 1, page=1
        )
    )

    assert len(items) == 3
    assert total == 10
    assert has_more is True


async def test_fetch_playable_tracks_liked() -> None:
    from bot.handlers.player import (
        _fetch_playable_tracks,
    )

    client = AsyncMock()
    client.get_liked_tracks = AsyncMock(
        return_value={
            "items": [
                {
                    "id": 1,
                    "source": "soundcloud",
                },
                {
                    "id": 2,
                    "processing_status": "active",
                },
                {
                    "id": 3,
                    "processing_status": "pending",
                },
            ]
        }
    )

    items, total, has_more = (
        await _fetch_playable_tracks(
            client, "liked", "tok", 1, page=1
        )
    )

    assert total == 2
    assert len(items) <= 3


async def test_fetch_playable_tracks_feed() -> None:
    from bot.handlers.player import (
        _fetch_playable_tracks,
    )

    client = AsyncMock()
    client.get_feed_tracks = AsyncMock(
        return_value={
            "items": _tracks(2),
            "total": 2,
        }
    )

    items, total, has_more = (
        await _fetch_playable_tracks(
            client, "feed", "tok", 1, page=1
        )
    )

    assert len(items) == 2
    assert total == 2
    assert has_more is False


# ------------------------------------------------------------------
# _is_file_id / _audio_input
# ------------------------------------------------------------------


def test_is_file_id_true() -> None:
    from bot.handlers.player import _is_file_id

    assert _is_file_id("AgACAgIAAxk") is True


def test_is_file_id_false_http() -> None:
    from bot.handlers.player import _is_file_id

    assert _is_file_id("https://example.com") is False


def test_audio_input_file_id() -> None:
    from bot.handlers.player import _audio_input

    result = _audio_input("AgACAgIAAxk", "Song")
    assert result == "AgACAgIAAxk"


def test_audio_input_url() -> None:
    from bot.handlers.player import _audio_input

    result = _audio_input(
        "https://example.com/song.mp3", "Song"
    )
    assert hasattr(result, "url")


# ------------------------------------------------------------------
# _resolve_audio
# ------------------------------------------------------------------


@patch("bot.handlers.player.get_cached_file_id")
async def test_resolve_audio_cached(
    mock_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _resolve_audio

    mock_cache.return_value = "cached_fid"
    client = AsyncMock()

    url, is_cached = await _resolve_audio(
        client, 1, "tok"
    )

    assert url == "cached_fid"
    assert is_cached is True


@patch("bot.handlers.player.get_cached_file_id")
async def test_resolve_audio_from_backend(
    mock_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _resolve_audio

    mock_cache.return_value = None
    client = AsyncMock()
    client.get_stream_url = AsyncMock(
        return_value="https://cdn.test/a.mp3"
    )

    url, is_cached = await _resolve_audio(
        client, 1, "tok"
    )

    assert url == "https://cdn.test/a.mp3"
    assert is_cached is False


@patch("bot.handlers.player.get_cached_file_id")
async def test_resolve_audio_backend_error(
    mock_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _resolve_audio

    mock_cache.return_value = None
    client = AsyncMock()
    client.get_stream_url = AsyncMock(
        side_effect=BackendError(500, "fail")
    )

    url, is_cached = await _resolve_audio(
        client, 1, "tok"
    )

    assert url is None
    assert is_cached is False


# ------------------------------------------------------------------
# _send_audio_batch
# ------------------------------------------------------------------


@patch("bot.handlers.player.set_cached_file_id")
@patch("bot.handlers.player.get_cached_file_id")
async def test_send_audio_batch_success(
    mock_get_cache: AsyncMock,
    mock_set_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _send_audio_batch

    mock_get_cache.return_value = None
    mock_set_cache.return_value = None

    bot = AsyncMock()
    msg = _audio_msg(10)
    bot.send_audio = AsyncMock(return_value=msg)

    client = AsyncMock()
    client.get_stream_url = AsyncMock(
        return_value="https://cdn/a.mp3"
    )

    ids = await _send_audio_batch(
        bot, client, 100, _tracks(1), "tok"
    )

    assert ids == [10]
    bot.send_audio.assert_awaited_once()
    mock_set_cache.assert_awaited_once()


@patch("bot.handlers.player.set_cached_file_id")
@patch("bot.handlers.player.get_cached_file_id")
async def test_send_audio_batch_skip_no_media(
    mock_get_cache: AsyncMock,
    mock_set_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _send_audio_batch

    mock_get_cache.return_value = None
    client = AsyncMock()
    client.get_stream_url = AsyncMock(
        side_effect=BackendError(404, "missing")
    )

    bot = AsyncMock()

    ids = await _send_audio_batch(
        bot, client, 100, _tracks(1), "tok"
    )

    assert ids == []
    bot.send_audio.assert_not_awaited()


@patch("bot.handlers.player.set_cached_file_id")
@patch("bot.handlers.player.get_cached_file_id")
async def test_send_audio_batch_send_exception(
    mock_get_cache: AsyncMock,
    mock_set_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _send_audio_batch

    mock_get_cache.return_value = "cached_fid"
    bot = AsyncMock()
    bot.send_audio = AsyncMock(
        side_effect=Exception("telegram error")
    )
    client = AsyncMock()

    ids = await _send_audio_batch(
        bot, client, 100, _tracks(1), "tok"
    )

    assert ids == []


# ------------------------------------------------------------------
# _edit_audio_batch
# ------------------------------------------------------------------


@patch("bot.handlers.player.set_cached_file_id")
@patch("bot.handlers.player.get_cached_file_id")
async def test_edit_audio_batch_edit_success(
    mock_get_cache: AsyncMock,
    mock_set_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _edit_audio_batch

    mock_get_cache.return_value = "cached_fid"
    bot = AsyncMock()
    bot.edit_message_media = AsyncMock()
    bot.delete_message = AsyncMock()
    client = AsyncMock()

    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.audio_message_ids = [10]

    new_ids = await _edit_audio_batch(
        bot, client, session, _tracks(1), "tok"
    )

    assert new_ids == [10]
    bot.edit_message_media.assert_awaited_once()


@patch("bot.handlers.player.set_cached_file_id")
@patch("bot.handlers.player.get_cached_file_id")
async def test_edit_audio_batch_edit_fails_fallback(
    mock_get_cache: AsyncMock,
    mock_set_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _edit_audio_batch

    mock_get_cache.return_value = "cached_fid"
    bot = AsyncMock()
    bot.edit_message_media = AsyncMock(
        side_effect=Exception("edit failed")
    )
    fallback_msg = _audio_msg(20)
    bot.send_audio = AsyncMock(
        return_value=fallback_msg
    )
    bot.delete_message = AsyncMock()
    client = AsyncMock()

    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.audio_message_ids = [10]

    new_ids = await _edit_audio_batch(
        bot, client, session, _tracks(1), "tok"
    )

    assert 20 in new_ids
    bot.send_audio.assert_awaited()


@patch("bot.handlers.player.set_cached_file_id")
@patch("bot.handlers.player.get_cached_file_id")
async def test_edit_audio_batch_new_track_appended(
    mock_get_cache: AsyncMock,
    mock_set_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _edit_audio_batch

    mock_get_cache.return_value = "cached_fid"
    bot = AsyncMock()
    new_msg = _audio_msg(30)
    bot.send_audio = AsyncMock(return_value=new_msg)
    bot.delete_message = AsyncMock()
    client = AsyncMock()

    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.audio_message_ids = []

    new_ids = await _edit_audio_batch(
        bot, client, session, _tracks(1), "tok"
    )

    assert new_ids == [30]


@patch("bot.handlers.player.set_cached_file_id")
@patch("bot.handlers.player.get_cached_file_id")
async def test_edit_audio_batch_deletes_extra(
    mock_get_cache: AsyncMock,
    mock_set_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _edit_audio_batch

    mock_get_cache.return_value = "cached_fid"
    bot = AsyncMock()
    bot.edit_message_media = AsyncMock()
    bot.delete_message = AsyncMock()
    client = AsyncMock()

    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.audio_message_ids = [10, 11, 12]

    new_ids = await _edit_audio_batch(
        bot, client, session, _tracks(1), "tok"
    )

    assert bot.delete_message.await_count == 2


# ------------------------------------------------------------------
# on_player_menu
# ------------------------------------------------------------------


async def test_on_player_menu() -> None:
    from bot.handlers.player import on_player_menu

    cb = _make_callback("menu:player")

    await on_player_menu(cb)

    cb.answer.assert_awaited_once()
    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "Плеер" in text


# ------------------------------------------------------------------
# on_player_source
# ------------------------------------------------------------------


@patch("bot.handlers.player._start_prefetch")
@patch(
    "bot.handlers.player.format_player_message",
    return_value="player_msg",
)
@patch("bot.handlers.player.set_cached_file_id", new_callable=AsyncMock)
@patch("bot.handlers.player.get_cached_file_id", new_callable=AsyncMock)
@patch("bot.handlers.player.player_control_kb")
@patch("bot.handlers.player._get_token")
@patch("bot.handlers.player.player_sessions")
@patch("bot.handlers.player.BackendClient")
async def test_on_player_source_success(
    mock_cls: MagicMock,
    mock_sessions: MagicMock,
    mock_get_token: AsyncMock,
    mock_kb: MagicMock,
    _mock_set_cached_file_id: AsyncMock,
    mock_get_cached_file_id: AsyncMock,
    mock_fmt: MagicMock,
    mock_prefetch: MagicMock,
) -> None:
    from bot.handlers.player import on_player_source

    mock_get_token.return_value = ("tok", 5)
    client = AsyncMock()
    client.get_my_tracks = AsyncMock(
        return_value={
            "items": _tracks(2),
            "total": 2,
        }
    )
    client.get_stream_url = AsyncMock(
        return_value="https://cdn/a.mp3"
    )
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )
    mock_get_cached_file_id.return_value = None

    mock_sessions.get.return_value = None
    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    mock_sessions.create.return_value = session

    cb = _make_callback("player:src:my")
    msg = _audio_msg(10)
    cb.bot.send_audio = AsyncMock(return_value=msg)
    ctrl = MagicMock()
    ctrl.message_id = 50
    cb.bot.send_message = AsyncMock(
        return_value=ctrl
    )

    await on_player_source(cb)

    cb.answer.assert_awaited()
    cb.bot.send_message.assert_awaited()


@patch("bot.handlers.player._get_token")
@patch("bot.handlers.player.player_sessions")
@patch("bot.handlers.player.BackendClient")
async def test_on_player_source_auth_fail(
    mock_cls: MagicMock,
    mock_sessions: MagicMock,
    mock_get_token: AsyncMock,
) -> None:
    from bot.handlers.player import on_player_source

    mock_get_token.side_effect = BackendError(
        401, "bad"
    )
    client = AsyncMock()
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )
    mock_sessions.get.return_value = None

    cb = _make_callback("player:src:my")

    await on_player_source(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "авторизоваться" in text


@patch("bot.handlers.player._get_token")
@patch("bot.handlers.player.player_sessions")
@patch("bot.handlers.player.BackendClient")
async def test_on_player_source_no_tracks(
    mock_cls: MagicMock,
    mock_sessions: MagicMock,
    mock_get_token: AsyncMock,
) -> None:
    from bot.handlers.player import on_player_source

    mock_get_token.return_value = ("tok", 5)
    client = AsyncMock()
    client.get_my_tracks = AsyncMock(
        return_value={"items": [], "total": 0}
    )
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )
    mock_sessions.get.return_value = None

    cb = _make_callback("player:src:my")

    await on_player_source(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "не найдено" in text.lower()


@patch("bot.handlers.player._get_token")
@patch("bot.handlers.player.player_sessions")
@patch("bot.handlers.player.BackendClient")
async def test_on_player_source_fetch_error(
    mock_cls: MagicMock,
    mock_sessions: MagicMock,
    mock_get_token: AsyncMock,
) -> None:
    from bot.handlers.player import on_player_source

    mock_get_token.return_value = ("tok", 5)
    client = AsyncMock()
    client.get_my_tracks = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )
    mock_sessions.get.return_value = None

    cb = _make_callback("player:src:my")

    await on_player_source(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "загрузить" in text.lower()


@patch("bot.handlers.player._get_token")
@patch("bot.handlers.player.player_sessions")
@patch("bot.handlers.player.BackendClient")
async def test_on_player_source_cleans_old_session(
    mock_cls: MagicMock,
    mock_sessions: MagicMock,
    mock_get_token: AsyncMock,
) -> None:
    from bot.handlers.player import on_player_source

    mock_get_token.return_value = ("tok", 5)
    old_session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    old_session.audio_message_ids = [10, 11]
    old_session.control_message_id = 20
    mock_sessions.get.return_value = old_session

    client = AsyncMock()
    client.get_my_tracks = AsyncMock(
        return_value={"items": [], "total": 0}
    )
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )

    cb = _make_callback("player:src:my")

    await on_player_source(cb)

    mock_sessions.remove.assert_called_once_with(1)
    assert cb.bot.delete_message.await_count >= 2


async def test_on_player_source_no_user() -> None:
    from bot.handlers.player import on_player_source

    cb = _make_callback("player:src:my")
    cb.from_user = None
    cb.data = "player:src:my"

    await on_player_source(cb)

    cb.answer.assert_awaited_once()


# ------------------------------------------------------------------
# on_player_next
# ------------------------------------------------------------------


async def test_on_player_next_expired_session(
) -> None:
    from bot.handlers.player import on_player_next

    cb = _make_callback("player:next")

    with patch(
        "bot.handlers.player.player_sessions"
    ) as mock_mgr:
        mock_mgr.get = MagicMock(return_value=None)
        await on_player_next(cb)

    cb.answer.assert_awaited()
    text = cb.answer.call_args[0][0]
    assert "Сессия" in text


async def test_on_player_next_no_user() -> None:
    from bot.handlers.player import on_player_next

    cb = _make_callback("player:next")
    cb.from_user = None

    await on_player_next(cb)

    cb.answer.assert_awaited_once()


@patch("bot.handlers.player._start_prefetch")
@patch(
    "bot.handlers.player.format_player_message",
    return_value="msg",
)
@patch("bot.handlers.player.player_control_kb")
@patch("bot.handlers.player._get_token")
@patch("bot.handlers.player.player_sessions")
@patch("bot.handlers.player.BackendClient")
async def test_on_player_next_with_prefetched(
    mock_cls: MagicMock,
    mock_sessions: MagicMock,
    mock_get_token: AsyncMock,
    mock_kb: MagicMock,
    mock_fmt: MagicMock,
    mock_prefetch: MagicMock,
) -> None:
    from bot.handlers.player import on_player_next

    mock_get_token.return_value = ("tok", 5)
    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.audio_message_ids = [10]
    session.control_message_id = 50
    session.track_ids = [1]
    session.page = 1
    session.has_more = True
    session.prefetched_tracks = _tracks(2)
    session.prefetched_total = 5
    session.prefetched_has_more = True

    mock_sessions.get.return_value = session

    client = AsyncMock()
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )

    cb = _make_callback("player:next")
    cb.bot.edit_message_media = AsyncMock()
    cb.bot.delete_message = AsyncMock()

    with patch(
        "bot.handlers.player."
        "_edit_audio_batch",
        new_callable=AsyncMock,
        return_value=[11, 12],
    ):
        await on_player_next(cb)

    assert session.page == 2
    assert session.has_more is True


@patch("bot.handlers.player._get_token")
@patch("bot.handlers.player.player_sessions")
@patch("bot.handlers.player.BackendClient")
async def test_on_player_next_no_tracks_left(
    mock_cls: MagicMock,
    mock_sessions: MagicMock,
    mock_get_token: AsyncMock,
) -> None:
    from bot.handlers.player import on_player_next

    mock_get_token.return_value = ("tok", 5)
    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.page = 3
    session.has_more = True
    session.prefetched_tracks = []
    mock_sessions.get.return_value = session

    client = AsyncMock()
    client.get_my_tracks = AsyncMock(
        return_value={"items": [], "total": 9}
    )
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )

    cb = _make_callback("player:next")

    await on_player_next(cb)

    cb.answer.assert_awaited()
    assert session.has_more is False


@patch("bot.handlers.player._get_token")
@patch("bot.handlers.player.player_sessions")
@patch("bot.handlers.player.BackendClient")
async def test_on_player_next_backend_error(
    mock_cls: MagicMock,
    mock_sessions: MagicMock,
    mock_get_token: AsyncMock,
) -> None:
    from bot.handlers.player import on_player_next

    mock_get_token.return_value = ("tok", 5)
    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.page = 1
    session.has_more = True
    session.prefetched_tracks = []
    mock_sessions.get.return_value = session

    client = AsyncMock()
    client.get_my_tracks = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )

    cb = _make_callback("player:next")

    await on_player_next(cb)

    cb.answer.assert_awaited()


# ------------------------------------------------------------------
# on_player_like
# ------------------------------------------------------------------


async def test_on_player_like_no_session() -> None:
    from bot.handlers.player import on_player_like

    cb = _make_callback("player:like:0")

    with patch(
        "bot.handlers.player.player_sessions"
    ) as m:
        m.get = MagicMock(return_value=None)
        await on_player_like(cb)

    text = cb.answer.call_args[0][0]
    assert "истекла" in text


async def test_on_player_like_no_user() -> None:
    from bot.handlers.player import on_player_like

    cb = _make_callback("player:like:0")
    cb.from_user = None
    cb.data = "player:like:0"

    await on_player_like(cb)

    cb.answer.assert_awaited_once()


async def test_on_player_like_invalid_index() -> None:
    from bot.handlers.player import on_player_like

    cb = _make_callback("player:like:abc")

    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.track_ids = [1, 2]

    with patch(
        "bot.handlers.player.player_sessions"
    ) as m:
        m.get = MagicMock(return_value=session)
        await on_player_like(cb)

    cb.answer.assert_awaited()


async def test_on_player_like_out_of_range() -> None:
    from bot.handlers.player import on_player_like

    cb = _make_callback("player:like:5")

    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.track_ids = [1, 2]

    with patch(
        "bot.handlers.player.player_sessions"
    ) as m:
        m.get = MagicMock(return_value=session)
        await on_player_like(cb)

    text = cb.answer.call_args[0][0]
    assert "не найден" in text


@patch("bot.handlers.player._get_token")
@patch("bot.handlers.player.BackendClient")
async def test_on_player_like_success(
    mock_cls: MagicMock,
    mock_get_token: AsyncMock,
) -> None:
    from bot.handlers.player import on_player_like

    mock_get_token.return_value = ("tok", 5)
    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.track_ids = [10, 20]
    session.internal_user_id = 5

    client = AsyncMock()
    client.toggle_like = AsyncMock(
        return_value={"liked": True}
    )
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )

    cb = _make_callback("player:like:0")

    with patch(
        "bot.handlers.player.player_sessions"
    ) as m:
        m.get = MagicMock(return_value=session)
        await on_player_like(cb)

    cb.answer.assert_awaited()
    text = cb.answer.call_args[0][0]
    assert "Лайк" in text


@patch("bot.handlers.player._get_token")
@patch("bot.handlers.player.BackendClient")
async def test_on_player_like_unlike(
    mock_cls: MagicMock,
    mock_get_token: AsyncMock,
) -> None:
    from bot.handlers.player import on_player_like

    mock_get_token.return_value = ("tok", 5)
    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.track_ids = [10]
    session.internal_user_id = 5

    client = AsyncMock()
    client.toggle_like = AsyncMock(
        return_value={"liked": False}
    )
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )

    cb = _make_callback("player:like:0")

    with patch(
        "bot.handlers.player.player_sessions"
    ) as m:
        m.get = MagicMock(return_value=session)
        await on_player_like(cb)

    text = cb.answer.call_args[0][0]
    assert "убран" in text


@patch("bot.handlers.player._get_token")
@patch("bot.handlers.player.BackendClient")
async def test_on_player_like_backend_error(
    mock_cls: MagicMock,
    mock_get_token: AsyncMock,
) -> None:
    from bot.handlers.player import on_player_like

    mock_get_token.return_value = ("tok", 5)
    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.track_ids = [10]
    session.internal_user_id = 5

    client = AsyncMock()
    client.toggle_like = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )

    cb = _make_callback("player:like:0")

    with patch(
        "bot.handlers.player.player_sessions"
    ) as m:
        m.get = MagicMock(return_value=session)
        await on_player_like(cb)

    text = cb.answer.call_args[0][0]
    assert "Ошибка" in text


# ------------------------------------------------------------------
# on_player_back
# ------------------------------------------------------------------


async def test_on_player_back_cleans_session(
) -> None:
    from bot.handlers.player import on_player_back

    mgr = PlayerSessionManager()
    session = mgr.create(
        chat_id=100, user_id=1, source="my"
    )
    session.audio_message_ids = [10, 11]

    cb = _make_callback("player:menu")

    with patch(
        "bot.handlers.player.player_sessions", mgr
    ):
        await on_player_back(cb)

    assert mgr.get(1) is None
    cb.message.edit_text.assert_awaited_once()


async def test_on_player_back_no_user() -> None:
    from bot.handlers.player import on_player_back

    cb = _make_callback("player:menu")
    cb.from_user = None

    await on_player_back(cb)

    cb.answer.assert_awaited_once()


async def test_on_player_back_no_session() -> None:
    from bot.handlers.player import on_player_back

    mgr = PlayerSessionManager()
    cb = _make_callback("player:menu")

    with patch(
        "bot.handlers.player.player_sessions", mgr
    ):
        await on_player_back(cb)

    cb.message.edit_text.assert_awaited_once()
    text = cb.message.edit_text.call_args[0][0]
    assert "Alice" in text


# ------------------------------------------------------------------
# _start_prefetch
# ------------------------------------------------------------------


async def test_start_prefetch_creates_task() -> None:
    from bot.handlers.player import _start_prefetch

    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.has_more = True

    with patch(
        "bot.handlers.player.asyncio.create_task"
    ) as mock_task:
        _start_prefetch(session, 1)
        mock_task.assert_called_once()


async def test_start_prefetch_skips_no_more() -> None:
    from bot.handlers.player import _start_prefetch

    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.has_more = False

    with patch(
        "bot.handlers.player.asyncio.create_task"
    ) as mock_task:
        _start_prefetch(session, 1)
        mock_task.assert_not_called()


# ------------------------------------------------------------------
# _prefetch_next
# ------------------------------------------------------------------


@patch("bot.handlers.player.get_cached_file_id")
@patch("bot.handlers.player.BackendClient")
async def test_prefetch_next_success(
    mock_cls: MagicMock,
    mock_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _prefetch_next

    mock_cache.return_value = "cached_fid"
    client = AsyncMock()
    client.get_internal_token = AsyncMock(
        return_value={
            "access_token": "tok",
            "user_id": 5,
        }
    )
    client.get_my_tracks = AsyncMock(
        return_value={
            "items": _tracks(2),
            "total": 5,
        }
    )
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )

    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.page = 1

    with patch(
        "bot.handlers.player.settings"
    ) as s:
        s.internal_api_secret = "sec"
        await _prefetch_next(session, 1)

    assert len(session.prefetched_tracks) == 2


@patch("bot.handlers.player.get_cached_file_id")
@patch("bot.handlers.player.BackendClient")
async def test_prefetch_next_empty(
    mock_cls: MagicMock,
    mock_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _prefetch_next

    client = AsyncMock()
    client.get_internal_token = AsyncMock(
        return_value={
            "access_token": "tok",
            "user_id": 5,
        }
    )
    client.get_my_tracks = AsyncMock(
        return_value={"items": [], "total": 0}
    )
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )

    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.page = 1

    with patch(
        "bot.handlers.player.settings"
    ) as s:
        s.internal_api_secret = "sec"
        await _prefetch_next(session, 1)

    assert session.prefetched_tracks == []
    assert session.prefetched_has_more is False


@patch("bot.handlers.player.BackendClient")
async def test_prefetch_next_exception_handled(
    mock_cls: MagicMock,
) -> None:
    from bot.handlers.player import _prefetch_next

    mock_cls.return_value.__aenter__ = AsyncMock(
        side_effect=Exception("fail")
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )

    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.page = 1

    await _prefetch_next(session, 1)


@patch("bot.handlers.player.get_cached_file_id")
@patch("bot.handlers.player.BackendClient")
async def test_prefetch_next_resolves_urls(
    mock_cls: MagicMock,
    mock_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _prefetch_next

    mock_cache.return_value = None
    client = AsyncMock()
    client.get_internal_token = AsyncMock(
        return_value={
            "access_token": "tok",
            "user_id": 5,
        }
    )
    client.get_my_tracks = AsyncMock(
        return_value={
            "items": _tracks(1),
            "total": 3,
        }
    )
    client.get_stream_url = AsyncMock(
        return_value="https://cdn/a.mp3"
    )
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )

    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.page = 1

    with patch(
        "bot.handlers.player.settings"
    ) as s:
        s.internal_api_secret = "sec"
        await _prefetch_next(session, 1)

    assert 1 in session.prefetched_urls


@patch("bot.handlers.player.get_cached_file_id")
@patch("bot.handlers.player.BackendClient")
async def test_prefetch_next_stream_error_skips(
    mock_cls: MagicMock,
    mock_cache: AsyncMock,
) -> None:
    from bot.handlers.player import _prefetch_next

    mock_cache.return_value = None
    client = AsyncMock()
    client.get_internal_token = AsyncMock(
        return_value={
            "access_token": "tok",
            "user_id": 5,
        }
    )
    client.get_my_tracks = AsyncMock(
        return_value={
            "items": _tracks(1),
            "total": 3,
        }
    )
    client.get_stream_url = AsyncMock(
        side_effect=BackendError(404, "nope")
    )
    mock_cls.return_value.__aenter__ = AsyncMock(
        return_value=client
    )
    mock_cls.return_value.__aexit__ = AsyncMock(
        return_value=False
    )

    session = PlayerSession(
        chat_id=100, user_id=1, source="my"
    )
    session.page = 1

    with patch(
        "bot.handlers.player.settings"
    ) as s:
        s.internal_api_secret = "sec"
        await _prefetch_next(session, 1)

    assert 1 not in session.prefetched_urls

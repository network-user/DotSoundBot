import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, InlineQuery

from bot.middlewares.throttling import (
    ThrottlingMiddleware,
)


def _make_event(user_id: int | None = None):
    event = MagicMock()
    if user_id is not None:
        event.from_user = MagicMock()
        event.from_user.id = user_id
    else:
        event.from_user = None
    return event


@pytest.mark.anyio
async def test_first_message_passes() -> None:
    mw = ThrottlingMiddleware(rate_limit=1.0)
    handler = AsyncMock(return_value="ok")
    event = _make_event(user_id=1)

    result = await mw(handler, event, {})

    assert result == "ok"
    handler.assert_awaited_once()


@pytest.mark.anyio
async def test_rapid_message_throttled() -> None:
    mw = ThrottlingMiddleware(rate_limit=10.0)
    handler = AsyncMock(return_value="ok")
    event = _make_event(user_id=1)

    await mw(handler, event, {})
    result = await mw(handler, event, {})

    assert result is None
    assert handler.await_count == 1


@pytest.mark.anyio
async def test_after_rate_limit_passes() -> None:
    mw = ThrottlingMiddleware(rate_limit=0.01)
    handler = AsyncMock(return_value="ok")
    event = _make_event(user_id=1)

    await mw(handler, event, {})

    base = time.monotonic()
    with patch(
        "bot.middlewares.throttling.time.monotonic",
        return_value=base + 1.0,
    ):
        result = await mw(handler, event, {})

    assert result == "ok"
    assert handler.await_count == 2


@pytest.mark.anyio
async def test_no_from_user_passes() -> None:
    mw = ThrottlingMiddleware(rate_limit=10.0)
    handler = AsyncMock(return_value="ok")
    event = _make_event(user_id=None)

    result = await mw(handler, event, {})

    assert result == "ok"
    handler.assert_awaited_once()


@pytest.mark.anyio
async def test_cleanup_removes_stale() -> None:
    mw = ThrottlingMiddleware(rate_limit=0.01)
    handler = AsyncMock(return_value="ok")
    event = _make_event(user_id=42)

    await mw(handler, event, {})

    assert 42 in mw._last_event

    base = time.monotonic()
    mw._last_cleanup = 0.0
    mw._last_event[42] = base - 200

    with patch(
        "bot.middlewares.throttling.time.monotonic",
        return_value=base + 1.0,
    ):
        event2 = _make_event(user_id=99)
        await mw(handler, event2, {})

    assert 42 not in mw._last_event


@pytest.mark.anyio
async def test_notify_throttled_callback() -> None:
    mw = ThrottlingMiddleware()
    cb = MagicMock(spec=CallbackQuery)
    cb.answer = AsyncMock()
    await mw._notify_throttled(cb)
    cb.answer.assert_awaited_once()


@pytest.mark.anyio
async def test_notify_throttled_inline() -> None:
    mw = ThrottlingMiddleware()
    iq = MagicMock(spec=InlineQuery)
    iq.answer = AsyncMock()
    await mw._notify_throttled(iq)
    iq.answer.assert_awaited_once()

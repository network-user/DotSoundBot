from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.middlewares.logging import LoggingMiddleware


def _make_update(
    update_id: int = 1,
    user_id: int | None = None,
    event_type: str = "message",
):
    update = MagicMock()
    update.update_id = update_id
    update.event_type = event_type

    if event_type == "message" and user_id:
        update.message = MagicMock()
        update.message.from_user = MagicMock()
        update.message.from_user.id = user_id
        update.callback_query = None
        update.inline_query = None
    elif event_type == "callback_query" and user_id:
        update.message = None
        update.callback_query = MagicMock()
        update.callback_query.from_user = MagicMock()
        update.callback_query.from_user.id = user_id
        update.inline_query = None
    else:
        update.message = None
        update.callback_query = None
        update.inline_query = None

    return update


@pytest.mark.anyio
async def test_handler_called_and_result_returned(
) -> None:
    mw = LoggingMiddleware()
    handler = AsyncMock(return_value="result")
    update = _make_update(user_id=1)

    result = await mw(handler, update, {})

    assert result == "result"
    handler.assert_awaited_once()


@pytest.mark.anyio
async def test_exception_propagates() -> None:
    mw = LoggingMiddleware()
    handler = AsyncMock(
        side_effect=ValueError("boom")
    )
    update = _make_update(user_id=1)

    with pytest.raises(ValueError, match="boom"):
        await mw(handler, update, {})


@pytest.mark.anyio
async def test_callback_query_user_extracted() -> None:
    mw = LoggingMiddleware()
    handler = AsyncMock(return_value=None)
    update = _make_update(
        user_id=42, event_type="callback_query"
    )

    await mw(handler, update, {})

    handler.assert_awaited_once()


@pytest.mark.anyio
async def test_inline_query_user_extracted() -> None:
    mw = LoggingMiddleware()
    handler = AsyncMock(return_value=None)
    update = _make_update(user_id=None, event_type="inline_query")
    update.inline_query = MagicMock()
    update.inline_query.from_user = MagicMock()
    update.inline_query.from_user.id = 99

    await mw(handler, update, {})

    handler.assert_awaited_once()

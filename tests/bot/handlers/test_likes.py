from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest

from bot.api.client import BackendError


def _make_callback(data: str, user_id: int = 1):
    cb = AsyncMock()
    cb.from_user = MagicMock()
    cb.from_user.id = user_id
    cb.data = data
    cb.answer = AsyncMock()
    return cb


@pytest.mark.anyio
@patch("bot.handlers.likes.BackendClient")
async def test_on_like_success(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.likes import on_like

    client = AsyncMock()
    client.toggle_like = AsyncMock(
        return_value={"liked": True}
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    cb = _make_callback("like_42")

    await on_like(cb)

    cb.answer.assert_awaited()
    text = cb.answer.call_args[0][0]
    assert "лайки" in text.lower() or "Добавлено" in text


@pytest.mark.anyio
@patch("bot.handlers.likes.BackendClient")
async def test_on_like_backend_error(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.likes import on_like

    client = AsyncMock()
    client.toggle_like = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    cb = _make_callback("like_42")

    await on_like(cb)

    cb.answer.assert_awaited()
    text = cb.answer.call_args[0][0]
    assert "Ошибка" in text


@pytest.mark.anyio
@patch("bot.handlers.likes.BackendClient")
async def test_on_dislike_success(
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.likes import on_dislike

    client = AsyncMock()
    client.toggle_dislike = AsyncMock(
        return_value={"disliked": True}
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    cb = _make_callback("dislike_10")

    await on_dislike(cb)

    cb.answer.assert_awaited()
    text = cb.answer.call_args[0][0]
    assert "Дизлайк" in text


@pytest.mark.anyio
async def test_on_like_invalid_data() -> None:
    from bot.handlers.likes import on_like

    cb = _make_callback("like_notanumber")

    await on_like(cb)

    cb.answer.assert_awaited_once()

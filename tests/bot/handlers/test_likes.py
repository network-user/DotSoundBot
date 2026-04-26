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
    cb.from_user.language_code = "ru"
    cb.data = data
    cb.answer = AsyncMock()
    return cb


def _patched_client(client_factory):
    cm = MagicMock()
    cm.return_value.__aenter__ = AsyncMock(
        return_value=client_factory()
    )
    cm.return_value.__aexit__ = AsyncMock(
        return_value=False
    )
    return cm


def _identity_response() -> dict:
    return {"access_token": "tok", "user_id": 5}


@pytest.mark.anyio
@patch("bot.handlers.likes.settings")
@patch("bot.handlers.likes.BackendClient")
async def test_on_like_success(
    mock_client_cls: MagicMock,
    mock_settings: MagicMock,
) -> None:
    from bot.handlers.likes import on_like

    mock_settings.internal_api_secret = "secret"
    client = AsyncMock()
    client.get_internal_token = AsyncMock(
        return_value=_identity_response()
    )
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
    assert (
        "лайки" in text.lower() or "Добавлено" in text
    )
    client.toggle_like.assert_awaited_once_with(
        5, 42, "tok"
    )


@pytest.mark.anyio
@patch("bot.handlers.likes.settings")
@patch("bot.handlers.likes.BackendClient")
async def test_on_like_backend_error(
    mock_client_cls: MagicMock,
    mock_settings: MagicMock,
) -> None:
    from bot.handlers.likes import on_like

    mock_settings.internal_api_secret = "secret"
    client = AsyncMock()
    client.get_internal_token = AsyncMock(
        return_value=_identity_response()
    )
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
@patch("bot.handlers.likes.settings")
@patch("bot.handlers.likes.BackendClient")
async def test_on_like_no_secret(
    mock_client_cls: MagicMock,
    mock_settings: MagicMock,
) -> None:
    from bot.handlers.likes import on_like

    mock_settings.internal_api_secret = ""
    client = AsyncMock()
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
    assert "Авторизация" in text


@pytest.mark.anyio
@patch("bot.handlers.likes.settings")
@patch("bot.handlers.likes.BackendClient")
async def test_on_dislike_success(
    mock_client_cls: MagicMock,
    mock_settings: MagicMock,
) -> None:
    from bot.handlers.likes import on_dislike

    mock_settings.internal_api_secret = "secret"
    client = AsyncMock()
    client.get_internal_token = AsyncMock(
        return_value=_identity_response()
    )
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
    client.toggle_dislike.assert_awaited_once_with(
        5, 10, "tok"
    )


@pytest.mark.anyio
async def test_on_like_invalid_data() -> None:
    from bot.handlers.likes import on_like

    cb = _make_callback("like_notanumber")

    await on_like(cb)

    cb.answer.assert_awaited_once()

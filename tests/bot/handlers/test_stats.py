from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest

from bot.api.client import BackendError


def _make_message(user_id: int = 1):
    msg = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.first_name = "Alice"
    msg.from_user.username = "alice"
    msg.from_user.last_name = None
    msg.from_user.language_code = "ru"
    msg.answer = AsyncMock()
    return msg


@pytest.mark.anyio
@patch("bot.handlers.stats.settings")
@patch("bot.handlers.stats.BackendClient")
async def test_cmd_mystats_success(
    mock_client_cls: MagicMock,
    mock_settings: MagicMock,
) -> None:
    from bot.handlers.stats import cmd_mystats

    mock_settings.backend_base_url = "http://test"
    mock_settings.mini_app_url = (
        "https://t.me/test_bot/app"
    )
    client = AsyncMock()
    client.post = AsyncMock(
        return_value={"id": 5}
    )
    client.get_user_stats = AsyncMock(
        return_value={
            "total_tracks": 3,
            "total_plays": 100,
            "top_tracks": [],
        }
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message()

    await cmd_mystats(msg)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "Alice" in text
    assert "3" in text


@pytest.mark.anyio
@patch("bot.handlers.stats.settings")
@patch("bot.handlers.stats.BackendClient")
async def test_cmd_mystats_backend_error(
    mock_client_cls: MagicMock,
    mock_settings: MagicMock,
) -> None:
    from bot.handlers.stats import cmd_mystats

    mock_settings.backend_base_url = "http://test"
    mock_settings.mini_app_url = (
        "https://t.me/test_bot/app"
    )
    client = AsyncMock()
    client.post = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message()

    await cmd_mystats(msg)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "Не удалось" in text


@pytest.mark.anyio
@patch("bot.handlers.stats.settings")
@patch("bot.handlers.stats.BackendClient")
async def test_cmd_mystats_with_top_tracks(
    mock_client_cls: MagicMock,
    mock_settings: MagicMock,
) -> None:
    from bot.handlers.stats import cmd_mystats

    mock_settings.backend_base_url = "http://test"
    mock_settings.mini_app_url = (
        "https://t.me/test_bot/app"
    )
    client = AsyncMock()
    client.post = AsyncMock(
        return_value={"id": 5}
    )
    client.get_user_stats = AsyncMock(
        return_value={
            "total_tracks": 2,
            "total_plays": 50,
            "top_tracks": [
                {
                    "title": "Hit",
                    "artist": "Star",
                    "play_count": 30,
                }
            ],
        }
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message()

    await cmd_mystats(msg)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "Hit" in text
    assert "Star" in text


@pytest.mark.anyio
async def test_cmd_mystats_without_from_user_noop() -> None:
    from bot.handlers.stats import cmd_mystats

    msg = AsyncMock()
    msg.from_user = None
    msg.answer = AsyncMock()

    await cmd_mystats(msg)

    msg.answer.assert_not_called()


@pytest.mark.anyio
async def test_on_my_stats_without_message_answers_only() -> None:
    from bot.handlers.stats import on_my_stats

    callback = AsyncMock()
    callback.from_user = MagicMock()
    callback.from_user.id = 42
    callback.from_user.language_code = "ru"
    callback.message = None
    callback.answer = AsyncMock()

    await on_my_stats(callback)

    callback.answer.assert_awaited_once()

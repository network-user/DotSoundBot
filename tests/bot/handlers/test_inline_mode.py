from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest

from bot.api.client import BackendError


def _make_inline_query(
    query_text: str = "",
    user_id: int = 1,
):
    q = AsyncMock()
    q.query = query_text
    q.from_user = MagicMock()
    q.from_user.id = user_id
    q.answer = AsyncMock()
    return q


@pytest.mark.anyio
@patch("bot.handlers.inline_mode.BackendClient")
@patch("bot.handlers.inline_mode.settings")
async def test_inline_search_with_results(
    mock_settings: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.inline_mode import (
        inline_search,
    )

    mock_settings.backend_base_url = "http://test"
    client = AsyncMock()
    client.get = AsyncMock(
        return_value={
            "items": [
                {
                    "id": 1,
                    "title": "Song",
                    "artist": "Art",
                    "play_count": 5,
                }
            ]
        }
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    query = _make_inline_query("Song")

    await inline_search(query)

    query.answer.assert_awaited_once()
    results = query.answer.call_args[1]["results"]
    assert len(results) == 1
    assert results[0].title == "Song"


@pytest.mark.anyio
async def test_inline_search_empty_query() -> None:
    from bot.handlers.inline_mode import (
        inline_search,
    )

    query = _make_inline_query("")

    await inline_search(query)

    query.answer.assert_awaited_once()
    assert query.answer.call_args[1]["results"] == []


@pytest.mark.anyio
@patch("bot.handlers.inline_mode.BackendClient")
@patch("bot.handlers.inline_mode.settings")
async def test_inline_search_backend_error(
    mock_settings: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.inline_mode import (
        inline_search,
    )

    mock_settings.backend_base_url = "http://test"
    client = AsyncMock()
    client.get = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    query = _make_inline_query("test")

    await inline_search(query)

    query.answer.assert_awaited_once()
    assert query.answer.call_args[1]["results"] == []

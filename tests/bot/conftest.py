from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.get_file = AsyncMock()
    bot.download_file = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def mock_backend_client():
    with patch("bot.api.client.BackendClient") as cls:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(
            return_value=instance
        )
        instance.__aexit__ = AsyncMock(
            return_value=False
        )
        cls.return_value = instance
        yield instance

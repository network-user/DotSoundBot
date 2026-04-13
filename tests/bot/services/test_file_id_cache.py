from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.setex = AsyncMock()
    return r


@pytest.fixture
def _patch_redis(mock_redis):
    with patch(
        "bot.services.file_id_cache._get_redis",
        return_value=mock_redis,
    ):
        yield mock_redis


@pytest.mark.anyio
async def test_get_cached_file_id_returns_none(
    _patch_redis,
    mock_redis,
) -> None:
    from bot.services.file_id_cache import (
        get_cached_file_id,
    )

    result = await get_cached_file_id(999)

    assert result is None
    mock_redis.get.assert_awaited_once()


@pytest.mark.anyio
async def test_set_then_get_returns_value(
    _patch_redis,
    mock_redis,
) -> None:
    from bot.services.file_id_cache import (
        get_cached_file_id,
        set_cached_file_id,
    )

    await set_cached_file_id(42, "file_abc")
    mock_redis.get.return_value = b"file_abc"

    result = await get_cached_file_id(42)

    assert result == "file_abc"


@pytest.mark.anyio
async def test_get_decodes_bytes(
    _patch_redis,
    mock_redis,
) -> None:
    from bot.services.file_id_cache import (
        get_cached_file_id,
    )

    mock_redis.get.return_value = b"cached_id_123"

    result = await get_cached_file_id(7)

    assert result == "cached_id_123"
    assert isinstance(result, str)

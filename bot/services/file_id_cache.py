from __future__ import annotations

import redis.asyncio as aioredis

from bot.config import settings

_FILE_ID_PREFIX = "tg_file_id:"
_FILE_ID_TTL = 7 * 86400

_redis: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url
        )
    return _redis


async def get_cached_file_id(
    track_id: int,
) -> str | None:
    r = await _get_redis()
    val = await r.get(
        f"{_FILE_ID_PREFIX}{track_id}"
    )
    if val is None:
        return None
    return (
        val.decode() if isinstance(val, bytes) else val
    )


async def set_cached_file_id(
    track_id: int, file_id: str
) -> None:
    r = await _get_redis()
    await r.setex(
        f"{_FILE_ID_PREFIX}{track_id}",
        _FILE_ID_TTL,
        file_id,
    )

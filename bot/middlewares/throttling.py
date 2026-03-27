import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_DEFAULT_RATE = 0.7


class ThrottlingMiddleware(BaseMiddleware):
    """Drop updates that arrive faster than `rate_limit` seconds per user."""

    def __init__(self, rate_limit: float = _DEFAULT_RATE) -> None:
        self._rate = rate_limit
        self._last_time: dict[int, float] = defaultdict(float)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id: int | None = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id

        if user_id is not None:
            now = time.monotonic()
            elapsed = now - self._last_time[user_id]
            if elapsed < self._rate:
                logger.warning(
                    "bot_update_throttled",
                    user_id=user_id,
                    elapsed_ms=round(elapsed * 1000, 1),
                )
                return None
            self._last_time[user_id] = now

        return await handler(event, data)

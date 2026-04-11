import time
from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message

logger: structlog.stdlib.BoundLogger = structlog.get_logger(
    __name__
)


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.7) -> None:
        self._rate_limit = rate_limit
        self._last_message: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[
            [Message, dict[str, Any]], Awaitable[Any]
        ],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.monotonic()
        last = self._last_message.get(user_id, 0.0)

        if now - last < self._rate_limit:
            logger.debug(
                "throttled", user_id=user_id
            )
            return None

        self._last_message[user_id] = now
        return await handler(event, data)

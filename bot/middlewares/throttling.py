import time
from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message

logger: structlog.stdlib.BoundLogger = structlog.get_logger(
    __name__
)


_CLEANUP_INTERVAL = 60.0
_ENTRY_TTL = 120.0


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.7) -> None:
        self._rate_limit = rate_limit
        self._last_message: dict[int, float] = {}
        self._last_cleanup: float = 0.0

    def _maybe_cleanup(self, now: float) -> None:
        if now - self._last_cleanup < _CLEANUP_INTERVAL:
            return
        self._last_cleanup = now
        stale = [
            uid
            for uid, ts in self._last_message.items()
            if now - ts > _ENTRY_TTL
        ]
        for uid in stale:
            del self._last_message[uid]

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
        self._maybe_cleanup(now)
        last = self._last_message.get(user_id, 0.0)

        if now - last < self._rate_limit:
            logger.debug(
                "throttled", user_id=user_id
            )
            return None

        self._last_message[user_id] = now
        return await handler(event, data)

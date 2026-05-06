import time
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    Message,
    TelegramObject,
)

from bot.i18n.core import resolve_lang, tr

logger: structlog.stdlib.BoundLogger = structlog.get_logger(
    __name__
)


_CLEANUP_INTERVAL = 60.0
_ENTRY_TTL = 120.0


def _throttled_hint(
    event: TelegramObject,
) -> str:
    u = getattr(
        event, "from_user", None
    ) or getattr(event, "user", None)
    return tr(
        "throttle.hint",
        resolve_lang(
            u.language_code if u else None
        ),
    )


class ThrottlingMiddleware(BaseMiddleware):
    """Per-user rate limiting for messages, callbacks and inline queries.

    Sliding-window suppression: if the same user fires events
    faster than ``rate_limit`` seconds, subsequent events are
    silently answered (callback) or hint-replied (message/inline)
    instead of running the handler.
    """

    def __init__(
        self,
        rate_limit: float = 0.7,
        callback_rate_limit: float | None = None,
    ) -> None:
        self._rate_limit = rate_limit
        self._callback_rate_limit = (
            callback_rate_limit
            if callback_rate_limit is not None
            else rate_limit
        )
        self._last_event: dict[int, float] = {}
        self._last_cleanup: float = 0.0

    def _maybe_cleanup(self, now: float) -> None:
        if now - self._last_cleanup < _CLEANUP_INTERVAL:
            return
        self._last_cleanup = now
        stale = [
            uid
            for uid, ts in self._last_event.items()
            if now - ts > _ENTRY_TTL
        ]
        for uid in stale:
            del self._last_event[uid]

    @staticmethod
    def _user_id(event: TelegramObject) -> int | None:
        for attr in ("from_user", "user"):
            user = getattr(event, attr, None)
            if user is not None and hasattr(user, "id"):
                return int(user.id)
        return None

    async def _notify_throttled(
        self, event: TelegramObject
    ) -> None:
        data_v = getattr(event, "data", None)
        q_v = getattr(event, "query", None)
        try:
            if isinstance(event, Message):
                await event.answer(
                    _throttled_hint(event)
                )
            elif (
                isinstance(event, CallbackQuery)
                or isinstance(data_v, str)
            ):
                await event.answer(
                    _throttled_hint(event), show_alert=False
                )
            elif (
                isinstance(event, InlineQuery)
                or isinstance(q_v, str)
            ):
                await event.answer(
                    [],
                    cache_time=1,
                    is_personal=True,
                    switch_pm_text=_throttled_hint(
                        event
                    ),
                    switch_pm_parameter="throttled",
                )
        except Exception:
            logger.debug(
                "throttle_notify_failed",
                event_type=type(event).__name__,
            )

    async def __call__(
        self,
        handler: Callable[
            [TelegramObject, dict[str, Any]],
            Awaitable[Any],
        ],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = self._user_id(event)
        if user_id is None:
            return await handler(event, data)

        now = time.monotonic()
        self._maybe_cleanup(now)
        last = self._last_event.get(user_id, 0.0)

        effective_rate_limit = self._rate_limit
        data_v = getattr(event, "data", None)
        if (
            isinstance(event, CallbackQuery)
            or isinstance(data_v, str)
        ):
            effective_rate_limit = (
                self._callback_rate_limit
            )

        if now - last < effective_rate_limit:
            logger.debug(
                "throttled",
                user_id=user_id,
                event_type=type(event).__name__,
            )
            await self._notify_throttled(event)
            return None

        self._last_event[user_id] = now
        return await handler(event, data)

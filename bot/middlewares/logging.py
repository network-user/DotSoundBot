import time
from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import Update

logger: structlog.stdlib.BoundLogger = structlog.get_logger(
    __name__
)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[
            [Update, dict[str, Any]], Awaitable[Any]
        ],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        structlog.contextvars.clear_contextvars()

        user_id = None
        if event.message and event.message.from_user:
            user_id = event.message.from_user.id
        elif (
            event.callback_query
            and event.callback_query.from_user
        ):
            user_id = event.callback_query.from_user.id
        elif (
            event.inline_query
            and event.inline_query.from_user
        ):
            user_id = event.inline_query.from_user.id

        structlog.contextvars.bind_contextvars(
            update_id=event.update_id,
            update_type=event.event_type,
            user_id=user_id,
        )

        start = time.perf_counter()
        try:
            result = await handler(event, data)
            duration_ms = round(
                (time.perf_counter() - start) * 1000, 2
            )
            logger.info(
                "update_handled",
                duration_ms=duration_ms,
            )
            return result
        except Exception as exc:
            duration_ms = round(
                (time.perf_counter() - start) * 1000, 2
            )
            logger.error(
                "update_handler_error",
                error=str(exc),
                duration_ms=duration_ms,
            )
            raise
        finally:
            structlog.contextvars.clear_contextvars()

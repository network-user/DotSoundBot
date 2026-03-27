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
    Update,
)

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


def _extract_user_id(event: TelegramObject) -> int | None:
    if isinstance(event, Update):
        if event.message and event.message.from_user:
            return event.message.from_user.id
        if event.callback_query and event.callback_query.from_user:
            return event.callback_query.from_user.id
        if event.inline_query and event.inline_query.from_user:
            return event.inline_query.from_user.id
    if isinstance(event, (Message, CallbackQuery, InlineQuery)):
        return event.from_user.id if event.from_user else None
    return None


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = _extract_user_id(event)
        update_type = type(event).__name__

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            user_id=user_id,
            update_type=update_type,
        )

        start = time.perf_counter()
        logger.info("bot_update_received")

        try:
            result = await handler(event, data)
            duration_ms = round(
                (time.perf_counter() - start) * 1000, 2
            )
            logger.info(
                "bot_update_handled",
                duration_ms=duration_ms,
            )
            return result
        except Exception as exc:
            logger.exception(
                "bot_handler_error",
                exc_info=exc,
            )
            raise
        finally:
            structlog.contextvars.clear_contextvars()

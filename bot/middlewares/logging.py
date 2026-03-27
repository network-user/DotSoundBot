import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id: int | None = None
        if isinstance(event, Update) and event.message:
            user_id = event.message.from_user.id if (
                event.message.from_user
            ) else None
        logger.debug(
            "update received",
            extra={"user_id": user_id},
        )
        return await handler(event, data)

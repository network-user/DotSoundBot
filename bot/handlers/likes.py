import structlog
from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.api.client import BackendClient, BackendError
from bot.config import settings

router = Router()
logger: structlog.stdlib.BoundLogger = structlog.get_logger(
    __name__
)


async def _resolve_internal_identity(
    client: BackendClient, telegram_id: int
) -> tuple[str, int] | None:
    secret = settings.internal_api_secret
    if not secret:
        logger.error(
            "internal_api_secret_missing",
            telegram_id=telegram_id,
        )
        return None
    try:
        data = await client.get_internal_token(
            telegram_id, secret
        )
    except BackendError as exc:
        logger.error(
            "internal_token_failed",
            status=exc.status_code,
            telegram_id=telegram_id,
        )
        return None
    token: str = data["access_token"]
    internal_id: int = data["user_id"]
    return token, internal_id


@router.callback_query(F.data.startswith("like_"))
async def on_like(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.data:
        await callback.answer()
        return

    telegram_id = callback.from_user.id
    try:
        track_id = int(
            callback.data.split("_", 1)[1]
        )
    except (IndexError, ValueError):
        await callback.answer()
        return

    structlog.contextvars.bind_contextvars(
        handler="on_like",
        telegram_id=telegram_id,
        track_id=track_id,
    )
    logger.info("like_callback_received")

    async with BackendClient() as client:
        identity = await _resolve_internal_identity(
            client, telegram_id
        )
        if identity is None:
            await callback.answer(
                "Авторизация не удалась.",
                show_alert=True,
            )
            return
        token, internal_user_id = identity

        try:
            data = await client.toggle_like(
                internal_user_id, track_id, token
            )
            liked: bool = data.get("liked", False)
            logger.info("like_toggled", liked=liked)
            text = (
                "Добавлено в лайки"
                if liked
                else "Убрано из лайков"
            )
            await callback.answer(
                text, show_alert=False
            )
        except BackendError as exc:
            logger.error(
                "like_backend_error",
                status=exc.status_code,
            )
            await callback.answer(
                "Ошибка. Попробуй ещё раз.",
                show_alert=True,
            )


@router.callback_query(F.data.startswith("dislike_"))
async def on_dislike(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user or not callback.data:
        await callback.answer()
        return

    telegram_id = callback.from_user.id
    try:
        track_id = int(
            callback.data.split("_", 1)[1]
        )
    except (IndexError, ValueError):
        await callback.answer()
        return

    structlog.contextvars.bind_contextvars(
        handler="on_dislike",
        telegram_id=telegram_id,
        track_id=track_id,
    )
    logger.info("dislike_callback_received")

    async with BackendClient() as client:
        identity = await _resolve_internal_identity(
            client, telegram_id
        )
        if identity is None:
            await callback.answer(
                "Авторизация не удалась.",
                show_alert=True,
            )
            return
        token, internal_user_id = identity

        try:
            data = await client.toggle_dislike(
                internal_user_id, track_id, token
            )
            disliked: bool = data.get("disliked", False)
            logger.info(
                "dislike_toggled", disliked=disliked
            )
            text = (
                "Дизлайк поставлен"
                if disliked
                else "Дизлайк убран"
            )
            await callback.answer(
                text, show_alert=False
            )
        except BackendError as exc:
            logger.error(
                "dislike_backend_error",
                status=exc.status_code,
            )
            await callback.answer(
                "Ошибка. Попробуй ещё раз.",
                show_alert=True,
            )

import structlog
from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.api.client import BackendClient, BackendError

router = Router()
logger: structlog.stdlib.BoundLogger = structlog.get_logger(
    __name__
)


@router.callback_query(F.data.startswith("like_"))
async def on_like(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.data:
        await callback.answer()
        return

    user_id = callback.from_user.id
    track_id = int(callback.data.split("_", 1)[1])

    structlog.contextvars.bind_contextvars(
        handler="on_like",
        user_id=user_id,
        track_id=track_id,
    )
    logger.info("like_callback_received")

    async with BackendClient() as client:
        try:
            data = await client.toggle_like(
                user_id, track_id
            )
            liked: bool = data.get("liked", False)
            logger.info("like_toggled", liked=liked)
            text = (
                "❤️ Добавлено в лайки!"
                if liked
                else "💔 Убрано из лайков"
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

    user_id = callback.from_user.id
    track_id = int(callback.data.split("_", 1)[1])

    structlog.contextvars.bind_contextvars(
        handler="on_dislike",
        user_id=user_id,
        track_id=track_id,
    )
    logger.info("dislike_callback_received")

    async with BackendClient() as client:
        try:
            data = await client.toggle_dislike(
                user_id, track_id
            )
            disliked: bool = data.get("disliked", False)
            logger.info(
                "dislike_toggled", disliked=disliked
            )
            text = (
                "👎 Дизлайк поставлен"
                if disliked
                else "👌 Дизлайк убран"
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

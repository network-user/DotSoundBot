import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, User

from bot.api.client import BackendClient, BackendError
from bot.config import settings
from bot.keyboards.inline import open_player_keyboard

router = Router()
logger: structlog.stdlib.BoundLogger = structlog.get_logger(
    __name__
)


async def _send_stats(
    user: User,
    target: Message,
) -> None:
    structlog.contextvars.bind_contextvars(
        telegram_id=user.id,
        handler="send_stats",
    )
    logger.info("stats_fetch_started")

    async with BackendClient() as client:
        try:
            user_data = await client.post(
                "/api/v1/users",
                json={
                    "telegram_id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            )
            internal_id: int = user_data["id"]
            stats = await client.get_user_stats(
                internal_id
            )
        except BackendError as exc:
            logger.error(
                "stats_backend_error",
                status=exc.status_code,
                detail=exc.detail,
            )
            await target.answer(
                "Не удалось получить статистику. "
                "Попробуй позже."
            )
            return

    total_tracks: int = stats["total_tracks"]
    total_plays: int = stats["total_plays"]
    top_tracks: list[dict] = stats.get(
        "top_tracks", []
    )

    logger.info(
        "stats_fetched",
        user_id=internal_id,
        total_tracks=total_tracks,
        total_plays=total_plays,
    )

    lines = [
        f"📊 <b>Твоя статистика, "
        f"{user.first_name}</b>\n",
        f"🎵 Загружено треков: "
        f"<b>{total_tracks}</b>",
        f"▶️ Всего прослушиваний: "
        f"<b>{total_plays}</b>",
    ]

    if top_tracks:
        lines.append("\n🏆 <b>Топ треков:</b>")
        for i, track in enumerate(top_tracks, 1):
            artist = (
                track.get("artist")
                or "Неизвестный исполнитель"
            )
            play_count = track.get("play_count", 0)
            title = track.get("title", "—")
            lines.append(
                f"{i}. {title} — {artist} "
                f"<i>({play_count} прослушиваний)</i>"
            )

    mini_app_url = (
        f"{settings.backend_base_url}/mini_app/"
    )
    await target.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=open_player_keyboard(mini_app_url),
    )


@router.message(Command("mystats"))
async def cmd_mystats(message: Message) -> None:
    if not message.from_user:
        return
    await _send_stats(message.from_user, message)


@router.callback_query(F.data == "my_stats")
async def on_my_stats(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    structlog.contextvars.bind_contextvars(
        handler="on_my_stats",
        telegram_id=callback.from_user.id,
    )
    logger.info("my_stats_callback")
    await callback.answer()
    if isinstance(callback.message, Message):
        await _send_stats(
            callback.from_user, callback.message
        )

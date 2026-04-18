import structlog
from aiogram import Router
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api.client import BackendClient, BackendError
from bot.config import settings
from bot.utils.formatting import safe_html

router = Router()
logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


def _track_keyboard(track_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❤️ Лайк",
        callback_data=f"like_{track_id}",
    )
    builder.button(
        text="💔 Дизлайк",
        callback_data=f"dislike_{track_id}",
    )
    builder.button(
        text="▶️ Слушать",
        url=(
            f"{settings.mini_app_url}"
            f"?track_id={track_id}"
        ),
    )
    builder.adjust(2, 1)
    return builder.as_markup()


@router.inline_query()
async def inline_search(query: InlineQuery) -> None:
    search_text = query.query.strip()
    user_id = (
        query.from_user.id if query.from_user else None
    )

    structlog.contextvars.bind_contextvars(
        handler="inline_search",
        user_id=user_id,
        query=search_text,
    )
    logger.info("inline_query_received")

    if not search_text:
        await query.answer(
            results=[],
            cache_time=1,
            switch_pm_text=(
                "Введите название трека или исполнителя"
            ),
            switch_pm_parameter="search",
        )
        return

    results: list[InlineQueryResultArticle] = []

    async with BackendClient() as client:
        try:
            data = await client.get(
                "/api/v1/tracks",
                params={"q": search_text, "size": 10},
            )
            tracks = data.get("items", [])
            logger.info(
                "inline_tracks_fetched", count=len(tracks)
            )
            for track in tracks:
                tid = track["id"]
                artist_raw = (
                    track.get("artist")
                    or "Неизвестный исполнитель"
                )
                title_raw = track.get(
                    "title", "Без названия"
                )
                play_count = track.get(
                    "play_count", 0
                )
                safe_title = safe_html(title_raw, 80)
                safe_artist = safe_html(
                    artist_raw, 60
                )
                results.append(
                    InlineQueryResultArticle(
                        id=str(tid),
                        title=title_raw,
                        description=(
                            f"{artist_raw} · "
                            f"{play_count} прослушиваний"
                        ),
                        input_message_content=(
                            InputTextMessageContent(
                                message_text=(
                                    f"🎵 <b>{safe_title}"
                                    f"</b>\n"
                                    f"👤 {safe_artist}"
                                ),
                                parse_mode="HTML",
                            )
                        ),
                        reply_markup=_track_keyboard(
                            tid
                        ),
                    )
                )
        except BackendError as exc:
            logger.error(
                "inline_backend_error",
                status=exc.status_code,
            )

    await query.answer(
        results=results,
        cache_time=10,
        is_personal=True,
    )

import structlog
from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from bot.api.client import BackendClient, BackendError

router = Router()
logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


@router.inline_query()
async def inline_search(query: InlineQuery) -> None:
    search_text = query.query.strip()
    user_id = query.from_user.id if query.from_user else None

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
            switch_pm_text="Введите название трека или исполнителя",
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
                "inline_tracks_fetched",
                count=len(tracks),
            )
            for track in tracks:
                artist = track.get("artist") or "Неизвестный исполнитель"
                title = track.get("title", "Без названия")
                results.append(
                    InlineQueryResultArticle(
                        id=str(track["id"]),
                        title=title,
                        description=artist,
                        input_message_content=InputTextMessageContent(
                            message_text=(
                                f"🎵 <b>{title}</b>\n👤 {artist}"
                            ),
                            parse_mode="HTML",
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

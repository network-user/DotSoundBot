import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, User

from bot.api.client import BackendClient, BackendError
from bot.config import settings
from bot.i18n.core import resolve_lang, tr
from bot.keyboards.inline import open_player_keyboard
from bot.utils.formatting import html_escape, safe_html

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
    lang = resolve_lang(
        user.language_code,
    )

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
                tr("stats.error", lang)
            )
            return

    total_tracks: int = stats.get(
        "total_tracks", 0
    )
    total_plays: int = stats.get(
        "total_plays", 0
    )
    top_tracks: list[dict] = stats.get(
        "top_tracks", []
    )

    logger.info(
        "stats_fetched",
        user_id=internal_id,
        total_tracks=total_tracks,
        total_plays=total_plays,
    )

    safe_first_name = html_escape(
        user.first_name or ""
    )
    pl_suf = tr("stats.plays_suffix", lang)
    lines = [
        tr("stats.opening", lang).format(
            name=safe_first_name
        ),
        tr("stats.tracks_line", lang).format(
            n=total_tracks
        ),
        tr("stats.plays_line", lang).format(
            n=total_plays
        ),
    ]

    if top_tracks:
        lines.append(tr("stats.top_header", lang))
        uartist = tr("stats.unknown_artist", lang)
        for i, track in enumerate(top_tracks, 1):
            artist = safe_html(
                track.get("artist") or uartist,
                40,
            )
            try:
                play_count = int(track.get("play_count", 0))
            except (TypeError, ValueError):
                play_count = 0
            title = safe_html(
                track.get("title", "—"), 60
            )
            lines.append(
                f"{i}. {title} — {artist} "
                f"<i>({play_count} {pl_suf})</i>"
            )

    await target.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=open_player_keyboard(
            settings.mini_app_url,
            lang,
        ),
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

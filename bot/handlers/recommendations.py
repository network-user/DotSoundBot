import structlog
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.api.client import BackendClient, BackendError
from bot.i18n.core import resolve_lang, tr
from bot.keyboards.inline import (
    back_to_menu_kb,
    daily_playlist_kb,
    weekly_playlist_kb,
)
from bot.utils.formatting import safe_html

router = Router()
logger: structlog.stdlib.BoundLogger = (
    structlog.get_logger(__name__)
)

_MAX_INTERNAL = 10
_MAX_EXTERNAL = 5
_MAX_GLOBAL_TOP = 5
_MAX_WEEKLY_INTERNAL = 15
_MAX_WEEKLY_EXTERNAL = 7


def _fmt_track(t: dict) -> str:
    title = safe_html(t.get("title") or "—")
    artist = safe_html(
        t.get("artist_name") or t.get("artist") or ""
    )
    return f"<b>{title}</b>" + (
        f" — {artist}" if artist else ""
    )


def _fmt_external(e: dict) -> str:
    title = safe_html(e.get("title") or "—")
    artist = safe_html(e.get("artist") or "")
    return f"<b>{title}</b>" + (
        f" — {artist}" if artist else ""
    )


@router.callback_query(F.data == "menu:daily_playlist")
async def on_daily_playlist(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    lang = resolve_lang(
        callback.from_user.language_code
    )
    await callback.answer()

    async with BackendClient() as client:
        try:
            data = await client.get_daily_playlist(
                callback.from_user.id
            )
        except BackendError as exc:
            logger.warning(
                "daily_playlist_fetch_failed",
                status=exc.status_code,
            )
            if callback.message and isinstance(
                callback.message, Message
            ):
                await callback.message.edit_text(
                    tr("recs.daily_error", lang),
                    reply_markup=back_to_menu_kb(lang),
                )
            return

    internal = data.get("internal_tracks") or []
    external = data.get("external_suggestions") or []
    global_top = data.get("global_top") or []

    lines: list[str] = [
        tr("recs.daily_header", lang),
    ]

    if internal:
        for i, t in enumerate(
            internal[:_MAX_INTERNAL], 1
        ):
            lines.append(f"{i}. {_fmt_track(t)}")
    else:
        lines.append(tr("recs.empty", lang))

    if external:
        lines.append(tr("recs.external", lang))
        for e in external[:_MAX_EXTERNAL]:
            lines.append(f"• {_fmt_external(e)}")

    if global_top:
        lines.append(tr("recs.top", lang))
        for t in global_top[:_MAX_GLOBAL_TOP]:
            lines.append(f"• {_fmt_track(t)}")

    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=daily_playlist_kb(lang),
        )


@router.callback_query(
    F.data == "menu:weekly_playlist"
)
async def on_weekly_playlist(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    wlang = resolve_lang(
        callback.from_user.language_code
    )
    await callback.answer()

    async with BackendClient() as client:
        try:
            data = await client.get_weekly_playlist(
                callback.from_user.id
            )
        except BackendError as exc:
            logger.warning(
                "weekly_playlist_fetch_failed",
                status=exc.status_code,
            )
            if callback.message and isinstance(
                callback.message, Message
            ):
                await callback.message.edit_text(
                    tr("recs.weekly_error", wlang),
                    reply_markup=back_to_menu_kb(wlang),
                )
            return

    internal = data.get("internal_tracks") or []
    external = data.get("external_suggestions") or []

    lines: list[str] = [
        tr("recs.weekly_header", wlang),
    ]

    if internal:
        for i, t in enumerate(
            internal[:_MAX_WEEKLY_INTERNAL], 1
        ):
            lines.append(f"{i}. {_fmt_track(t)}")
    else:
        lines.append(tr("recs.empty", wlang))

    if external:
        lines.append(tr("recs.external_week", wlang))
        for e in external[:_MAX_WEEKLY_EXTERNAL]:
            lines.append(f"• {_fmt_external(e)}")

    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=weekly_playlist_kb(wlang),
        )


@router.callback_query(F.data == "rec:daily:refresh")
async def on_refresh_daily(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    rlang = resolve_lang(
        callback.from_user.language_code
    )

    async with BackendClient() as client:
        try:
            await client.refresh_daily_playlist(
                callback.from_user.id
            )
            await callback.answer(
                tr("recs.refreshed", rlang),
                show_alert=True,
            )
        except BackendError as exc:
            if exc.status_code == 403:
                msg = tr("recs.admin_only", rlang)
            else:
                msg = tr("recs.refresh_error", rlang)
                logger.warning(
                    "daily_refresh_failed",
                    status=exc.status_code,
                )
            await callback.answer(
                msg, show_alert=True
            )

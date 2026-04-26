import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.api.client import BackendClient, BackendError
from bot.i18n.core import resolve_lang, tr
from bot.keyboards.inline import main_menu_kb, playlists_keyboard
from bot.utils.formatting import html_escape, safe_html

router = Router()
logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


class CreatePlaylistStates(StatesGroup):
    waiting_for_name = State()


@router.callback_query(F.data == "create_playlist")
async def on_create_playlist(
    callback: CallbackQuery, state: FSMContext
) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    structlog.contextvars.bind_contextvars(
        handler="on_create_playlist",
        user_id=callback.from_user.id,
    )
    logger.info("create_playlist_callback")
    await callback.answer()
    await state.set_state(CreatePlaylistStates.waiting_for_name)
    lang = resolve_lang(
        callback.from_user.language_code
    )
    if callback.message and isinstance(callback.message, Message):
        await callback.message.answer(
            tr("playlists.ask_name", lang)
        )


@router.message(CreatePlaylistStates.waiting_for_name)
async def on_playlist_name_received(
    message: Message, state: FSMContext
) -> None:
    if not message.from_user or not message.text:
        return
    lang = resolve_lang(
        message.from_user.language_code
    )

    if message.text.startswith("/"):
        await state.clear()
        return

    name = message.text.strip()
    if not name:
        await message.answer(
            tr("playlists.name_empty", lang)
        )
        return

    await state.clear()
    structlog.contextvars.bind_contextvars(
        handler="on_playlist_name_received",
        user_id=message.from_user.id,
        name=name,
    )
    logger.info("playlist_name_received")

    async with BackendClient() as client:
        try:
            playlist = await client.create_playlist(
                owner_id=message.from_user.id,
                name=name,
            )
            logger.info(
                "playlist_created",
                playlist_id=playlist.get("id"),
            )
            en = html_escape(name)
            await message.answer(
                tr("playlists.created", lang).format(
                    name=en
                ),
                parse_mode="HTML",
                reply_markup=main_menu_kb(lang),
            )
        except BackendError as exc:
            logger.error(
                "playlist_create_failed",
                status=exc.status_code,
                detail=exc.detail,
            )
            await message.answer(
                tr("playlists.create_error", lang)
            )


@router.callback_query(F.data.startswith("playlist_"))
async def on_playlist_selected(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user:
        await callback.answer()
        return

    raw = callback.data or ""
    playlist_id_str = raw.removeprefix("playlist_")
    if not playlist_id_str.isdigit():
        await callback.answer()
        return

    playlist_id = int(playlist_id_str)
    lang = resolve_lang(
        callback.from_user.language_code
    )
    structlog.contextvars.bind_contextvars(
        handler="on_playlist_selected",
        user_id=callback.from_user.id,
        playlist_id=playlist_id,
    )
    logger.info("playlist_selected")

    async with BackendClient() as client:
        try:
            detail = await client.get(
                f"/api/v1/playlists/{playlist_id}"
            )
            tracks = detail.get("tracks", [])
            nempty = tr("playlists.no_tracks", lang)
            tracks_text = (
                "\n".join(
                    f"🎵 {t.get('title', 'Unknown')}"
                    for t in tracks[:10]
                )
                if tracks
                else nempty
            )
            await callback.answer()
            if callback.message and isinstance(
                callback.message, Message
            ):
                pls = await client.get_user_playlists(
                    callback.from_user.id
                )
                pnm = safe_html(
                    detail.get("name", ""), 120
                )
                await callback.message.answer(
                    f"▤ <b>{pnm}</b>\n\n"
                    f"{tracks_text}",
                    parse_mode="HTML",
                    reply_markup=playlists_keyboard(
                        pls, lang
                    ),
                )
        except BackendError as exc:
            logger.error(
                "playlist_detail_failed",
                status=exc.status_code,
            )
            await callback.answer(
                tr("playlists.view_error", lang),
                show_alert=True,
            )

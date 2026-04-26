from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog
from aiogram import Bot, F, Router
from aiogram.types import (
    CallbackQuery,
    InputMediaAudio,
    Message,
    URLInputFile,
)

from bot.api.client import (
    BackendClient,
    BackendError,
)
from bot.config import settings
from bot.i18n.core import resolve_lang, tr
from bot.keyboards.inline import (
    main_menu_kb,
    player_control_kb,
    player_source_kb,
)
from bot.services.file_id_cache import (
    get_cached_file_id,
    set_cached_file_id,
)
from bot.services.player_session import (
    PlayerSession,
    player_sessions,
)
from bot.utils.formatting import (
    format_main_menu_welcome,
    format_player_message,
)

router = Router()
logger: structlog.stdlib.BoundLogger = (
    structlog.get_logger(__name__)
)

_BATCH_SIZE = 3
_TOKEN_CACHE_TTL = 720

_token_cache: dict[int, tuple[str, int, float]] = {}


async def _get_token(
    client: BackendClient, telegram_id: int
) -> tuple[str, int]:
    entry = _token_cache.get(telegram_id)
    if entry:
        token, uid, issued_at = entry
        if time.time() - issued_at < _TOKEN_CACHE_TTL:
            return token, uid

    data = await client.get_internal_token(
        telegram_id, settings.internal_api_secret
    )
    token: str = data["access_token"]
    uid: int = data["user_id"]
    _token_cache[telegram_id] = (
        token,
        uid,
        time.time(),
    )
    return token, uid


async def _fetch_playable_tracks(
    client: BackendClient,
    source: str,
    token: str,
    internal_user_id: int,
    page: int,
) -> tuple[list[dict[str, Any]], int, bool]:
    if source == "my":
        data = await client.get_my_tracks(
            token,
            page=page,
            size=_BATCH_SIZE,
            playable=True,
        )
        items: list[dict[str, Any]] = data["items"]
        total: int = data["total"]
        has_more = page * _BATCH_SIZE < total
        return items, total, has_more

    if source == "liked":
        data = await client.get_liked_tracks(
            internal_user_id, token
        )
        all_items = data.get("items", [])
        playable = [
            t
            for t in all_items
            if t.get("source") == "soundcloud"
            or t.get("processing_status") == "active"
        ]
        total = len(playable)
        start = (page - 1) * _BATCH_SIZE
        end_idx = start + _BATCH_SIZE
        batch = playable[start:end_idx]
        has_more = end_idx < total
        return batch, total, has_more

    data = await client.get_feed_tracks(
        page=page,
        size=_BATCH_SIZE,
        playable=True,
    )
    items = data["items"]
    total = data["total"]
    has_more = page * _BATCH_SIZE < total
    return items, total, has_more


def _is_file_id(value: str) -> bool:
    return not value.startswith(
        ("http://", "https://")
    )


def _audio_input(
    value: str, title: str
) -> str | URLInputFile:
    if _is_file_id(value):
        return value
    return URLInputFile(
        value, filename=f"{title}.mp3"
    )


async def _resolve_audio(
    client: BackendClient,
    track_id: int,
    token: str,
    prefetched: dict[int, str] | None = None,
) -> tuple[str | None, bool]:
    cached = await get_cached_file_id(track_id)
    if cached:
        return cached, True
    if prefetched and track_id in prefetched:
        return prefetched[track_id], False
    try:
        url = await client.get_stream_url(
            track_id, token
        )
        return url, False
    except BackendError:
        logger.warning(
            "stream_url_failed", track_id=track_id
        )
        return None, False


async def _send_audio_batch(
    bot: Bot,
    client: BackendClient,
    chat_id: int,
    tracks: list[dict[str, Any]],
    token: str,
    lang: str,
) -> list[int]:
    message_ids: list[int] = []
    no_title = tr("fmt.untitled", lang)
    for track in tracks:
        track_id: int = track["id"]
        title = track.get("title", no_title)
        artist = track.get("artist") or track.get(
            "performer", ""
        )

        media_src, is_cached = await _resolve_audio(
            client, track_id, token
        )
        if not media_src:
            continue

        try:
            audio = _audio_input(media_src, title)
            msg = await bot.send_audio(
                chat_id=chat_id,
                audio=audio,
                title=title,
                performer=artist or None,
            )
        except Exception:
            logger.warning(
                "send_audio_failed",
                track_id=track_id,
            )
            continue

        if (
            not is_cached
            and msg.audio
            and msg.audio.file_id
        ):
            await set_cached_file_id(
                track_id, msg.audio.file_id
            )
        message_ids.append(msg.message_id)
    return message_ids


async def _edit_audio_batch(
    bot: Bot,
    client: BackendClient,
    session: PlayerSession,
    tracks: list[dict[str, Any]],
    token: str,
    lang: str,
    prefetched: dict[int, str] | None = None,
) -> list[int]:
    new_ids: list[int] = []
    no_title = tr("fmt.untitled", lang)
    for i, track in enumerate(tracks):
        track_id: int = track["id"]
        title = track.get("title", no_title)
        artist = track.get("artist") or track.get(
            "performer", ""
        )

        media_src, is_cached = await _resolve_audio(
            client, track_id, token, prefetched
        )
        if not media_src:
            continue

        audio = _audio_input(media_src, title)
        msg_id: int | None = None

        if i < len(session.audio_message_ids):
            try:
                await bot.edit_message_media(
                    chat_id=session.chat_id,
                    message_id=(
                        session.audio_message_ids[i]
                    ),
                    media=InputMediaAudio(
                        media=audio,
                        title=title,
                        performer=artist or None,
                    ),
                )
                msg_id = session.audio_message_ids[i]
            except Exception:
                logger.warning(
                    "edit_media_failed",
                    message_id=(
                        session.audio_message_ids[i]
                    ),
                )
                if not is_cached:
                    fresh, _ = await _resolve_audio(
                        client, track_id, token
                    )
                    if fresh:
                        audio = _audio_input(
                            fresh, title
                        )

                try:
                    msg = await bot.send_audio(
                        chat_id=session.chat_id,
                        audio=audio,
                        title=title,
                        performer=artist or None,
                    )
                    msg_id = msg.message_id
                    if (
                        not is_cached
                        and msg.audio
                        and msg.audio.file_id
                    ):
                        await set_cached_file_id(
                            track_id,
                            msg.audio.file_id,
                        )
                except Exception:
                    logger.error(
                        "fallback_send_failed",
                        track_id=track_id,
                    )
        else:
            try:
                msg = await bot.send_audio(
                    chat_id=session.chat_id,
                    audio=audio,
                    title=title,
                    performer=artist or None,
                )
                msg_id = msg.message_id
                if (
                    not is_cached
                    and msg.audio
                    and msg.audio.file_id
                ):
                    await set_cached_file_id(
                        track_id, msg.audio.file_id
                    )
            except Exception:
                logger.error(
                    "send_audio_failed",
                    track_id=track_id,
                )

        if msg_id is not None:
            new_ids.append(msg_id)

    for j in range(
        len(tracks), len(session.audio_message_ids)
    ):
        try:
            await bot.delete_message(
                session.chat_id,
                session.audio_message_ids[j],
            )
        except Exception:
            pass

    return new_ids


async def _prefetch_next(
    session: PlayerSession,
    telegram_id: int,
) -> None:
    try:
        async with BackendClient() as client:
            token, uid = await _get_token(
                client, telegram_id
            )
            tracks, total, has_more = (
                await _fetch_playable_tracks(
                    client,
                    session.source,
                    token,
                    session.internal_user_id or uid,
                    page=session.page + 1,
                )
            )
            if not tracks:
                session.prefetched_tracks = []
                session.prefetched_has_more = False
                return

            urls: dict[int, str] = {}
            for t in tracks:
                tid: int = t["id"]
                cached = await get_cached_file_id(tid)
                if cached:
                    urls[tid] = cached
                else:
                    try:
                        url = (
                            await client.get_stream_url(
                                tid, token
                            )
                        )
                        urls[tid] = url
                    except BackendError:
                        pass

            session.prefetched_tracks = tracks
            session.prefetched_urls = urls
            session.prefetched_total = total
            session.prefetched_has_more = has_more
            logger.debug(
                "prefetch_complete",
                page=session.page + 1,
                count=len(tracks),
            )
    except Exception:
        logger.warning("prefetch_failed")


def _start_prefetch(
    session: PlayerSession,
    telegram_id: int,
) -> None:
    if session.has_more:
        asyncio.create_task(
            _prefetch_next(session, telegram_id)
        )


@router.callback_query(F.data == "menu:player")
async def on_player_menu(
    callback: CallbackQuery,
) -> None:
    await callback.answer()
    if not callback.from_user:
        return
    lang = resolve_lang(
        callback.from_user.language_code
    )
    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            tr("player.title_prompt", lang),
            reply_markup=player_source_kb(lang),
        )


@router.callback_query(
    F.data.startswith("player:src:")
)
async def on_player_source(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user or not callback.data:
        await callback.answer()
        return
    lang = resolve_lang(
        callback.from_user.language_code
    )
    await callback.answer(
        tr("player.loading", lang)
    )

    source = callback.data.split(":")[-1]
    telegram_id = callback.from_user.id
    chat_id = (
        callback.message.chat.id
        if callback.message
        else telegram_id
    )

    old_session = player_sessions.get(telegram_id)
    if old_session:
        for mid in old_session.audio_message_ids:
            try:
                await callback.bot.delete_message(
                    old_session.chat_id, mid
                )
            except Exception:
                pass
        if old_session.control_message_id:
            try:
                await callback.bot.delete_message(
                    old_session.chat_id,
                    old_session.control_message_id,
                )
            except Exception:
                pass
        player_sessions.remove(telegram_id)

    async with BackendClient() as client:
        try:
            token, internal_uid = await _get_token(
                client, telegram_id
            )
        except BackendError:
            if callback.message and isinstance(
                callback.message, Message
            ):
                await callback.message.edit_text(
                    tr("player.auth_failed", lang),
                    reply_markup=main_menu_kb(lang),
                )
            return

        try:
            tracks, total, has_more = (
                await _fetch_playable_tracks(
                    client,
                    source,
                    token,
                    internal_uid,
                    page=1,
                )
            )
        except BackendError:
            if callback.message and isinstance(
                callback.message, Message
            ):
                await callback.message.edit_text(
                    tr("player.tracks_error", lang),
                    reply_markup=main_menu_kb(lang),
                )
            return

        if not tracks:
            if callback.message and isinstance(
                callback.message, Message
            ):
                await callback.message.edit_text(
                    tr("player.no_tracks", lang),
                    reply_markup=main_menu_kb(lang),
                )
            return

        if callback.message and isinstance(
            callback.message, Message
        ):
            try:
                await callback.message.delete()
            except Exception:
                pass

        msg_ids = await _send_audio_batch(
            callback.bot,
            client,
            chat_id,
            tracks,
            token,
            lang,
        )

    text = format_player_message(
        source,
        tracks,
        page=1,
        total=total,
        lang=lang,
    )
    control_msg = await callback.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        reply_markup=player_control_kb(
            len(msg_ids), has_more, lang
        ),
    )

    session = player_sessions.create(
        chat_id=chat_id,
        user_id=telegram_id,
        source=source,
    )
    session.internal_user_id = internal_uid
    session.audio_message_ids = msg_ids
    session.control_message_id = (
        control_msg.message_id
    )
    session.track_ids = [t["id"] for t in tracks]
    session.page = 1
    session.has_more = has_more
    session.touch()

    _start_prefetch(session, telegram_id)


@router.callback_query(F.data == "player:next")
async def on_player_next(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    lang = resolve_lang(
        callback.from_user.language_code
    )

    telegram_id = callback.from_user.id
    session = player_sessions.get(telegram_id)
    if not session:
        await callback.answer(
            tr("player.session_expired", lang)
        )
        return

    await callback.answer(
        tr("player.loading", lang)
    )
    session.touch()

    prefetched_urls: dict[int, str] | None = None
    if session.prefetched_tracks:
        tracks = session.prefetched_tracks
        total = session.prefetched_total
        has_more = session.prefetched_has_more
        prefetched_urls = (
            session.prefetched_urls or None
        )

        session.prefetched_tracks = []
        session.prefetched_urls = {}
        session.prefetched_total = 0
        session.prefetched_has_more = False
    else:
        async with BackendClient() as client:
            token, _ = await _get_token(
                client, telegram_id
            )
            try:
                tracks, total, has_more = (
                    await _fetch_playable_tracks(
                        client,
                        session.source,
                        token,
                        session.internal_user_id,
                        page=session.page + 1,
                    )
                )
            except BackendError:
                await callback.answer(
                    tr("player.load_page_error", lang)
                )
                return

    if not tracks:
        await callback.answer(
            tr("player.no_more", lang)
        )
        session.has_more = False
        return

    async with BackendClient() as client:
        token, _ = await _get_token(
            client, telegram_id
        )
        new_ids = await _edit_audio_batch(
            callback.bot,
            client,
            session,
            tracks,
            token,
            lang,
            prefetched=prefetched_urls,
        )

    session.page += 1
    session.audio_message_ids = new_ids
    session.track_ids = [t["id"] for t in tracks]
    session.has_more = has_more

    text = format_player_message(
        session.source,
        tracks,
        page=session.page,
        total=total,
        lang=lang,
    )
    try:
        await callback.bot.edit_message_text(
            chat_id=session.chat_id,
            message_id=session.control_message_id,
            text=text,
            parse_mode="HTML",
            reply_markup=player_control_kb(
                len(new_ids), has_more, lang
            ),
        )
    except Exception:
        pass

    _start_prefetch(session, telegram_id)


@router.callback_query(
    F.data.startswith("player:like:")
)
async def on_player_like(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user or not callback.data:
        await callback.answer()
        return

    lang = resolve_lang(
        callback.from_user.language_code
    )
    telegram_id = callback.from_user.id
    session = player_sessions.get(telegram_id)
    if not session:
        await callback.answer(
            tr("player.session_short", lang)
        )
        return

    idx_str = callback.data.split(":")[-1]
    try:
        idx = int(idx_str)
    except ValueError:
        await callback.answer()
        return

    if idx < 0 or idx >= len(session.track_ids):
        await callback.answer(
            tr("player.track_missing", lang)
        )
        return

    track_id = session.track_ids[idx]
    session.touch()

    async with BackendClient() as client:
        try:
            token, uid = await _get_token(
                client, telegram_id
            )
            result = await client.toggle_like(
                session.internal_user_id or uid,
                track_id,
                token,
            )
            liked = result.get("liked", False)
            await callback.answer(
                tr("player.like_on", lang)
                if liked
                else tr("player.like_off", lang)
            )
        except BackendError:
            await callback.answer(
                tr("player.like_error", lang)
            )


@router.callback_query(F.data == "player:menu")
async def on_player_back(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    await callback.answer()

    telegram_id = callback.from_user.id
    session = player_sessions.get(telegram_id)

    if session:
        for mid in session.audio_message_ids:
            try:
                await callback.bot.delete_message(
                    session.chat_id, mid
                )
            except Exception:
                pass
        player_sessions.remove(telegram_id)

    if callback.message and isinstance(
        callback.message, Message
    ):
        name = callback.from_user.first_name
        olang = resolve_lang(
            callback.from_user.language_code
        )
        await callback.message.edit_text(
            format_main_menu_welcome(name, olang),
            reply_markup=main_menu_kb(olang),
        )

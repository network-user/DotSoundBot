from __future__ import annotations

from typing import Any

import structlog
from aiogram import Bot, F, Router
from aiogram.types import (
    CallbackQuery,
    InputMediaAudio,
    Message,
    URLInputFile,
)

from bot.api.client import BackendClient, BackendError
from bot.config import settings
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
    format_player_message,
)

router = Router()
logger: structlog.stdlib.BoundLogger = (
    structlog.get_logger(__name__)
)

_BATCH_SIZE = 3
_TOKEN_CACHE_TTL = 720

_token_cache: dict[int, tuple[str, float]] = {}


async def _get_token(
    client: BackendClient, telegram_id: int
) -> str:
    import time

    entry = _token_cache.get(telegram_id)
    if entry:
        token, issued_at = entry
        if time.time() - issued_at < _TOKEN_CACHE_TTL:
            return token

    data = await client.get_internal_token(
        telegram_id, settings.internal_api_secret
    )
    token = data["access_token"]
    _token_cache[telegram_id] = (
        token,
        time.time(),
    )
    return token


async def _fetch_tracks(
    client: BackendClient,
    source: str,
    telegram_id: int,
    token: str,
    user_id: int,
    page: int,
) -> tuple[list[dict[str, Any]], int, bool]:
    if source == "my":
        data = await client.get_my_tracks(
            token, page=page, size=_BATCH_SIZE
        )
        items: list[dict[str, Any]] = data["items"]
        total: int = data["total"]
        has_more = page * _BATCH_SIZE < total
        return items, total, has_more

    if source == "liked":
        data = await client.get_liked_tracks(
            user_id, token
        )
        items = data.get("items", [])
        total = data.get("total", len(items))
        start = (page - 1) * _BATCH_SIZE
        end = start + _BATCH_SIZE
        batch = items[start:end]
        has_more = end < len(items)
        return batch, total, has_more

    data = await client.get_feed_tracks(
        page=page, size=_BATCH_SIZE
    )
    items = data["items"]
    total = data["total"]
    has_more = page * _BATCH_SIZE < total
    return items, total, has_more


async def _send_audio_batch(
    bot: Bot,
    client: BackendClient,
    chat_id: int,
    tracks: list[dict[str, Any]],
    token: str,
) -> list[int]:
    message_ids: list[int] = []
    for track in tracks:
        track_id: int = track["id"]
        title = track.get("title", "Без названия")
        artist = track.get("artist") or track.get(
            "performer", ""
        )

        cached_fid = await get_cached_file_id(
            track_id
        )
        if cached_fid:
            msg = await bot.send_audio(
                chat_id=chat_id,
                audio=cached_fid,
                title=title,
                performer=artist or None,
            )
        else:
            try:
                url = await client.get_stream_url(
                    track_id, token
                )
            except BackendError:
                logger.warning(
                    "stream_url_failed",
                    track_id=track_id,
                )
                continue
            msg = await bot.send_audio(
                chat_id=chat_id,
                audio=URLInputFile(
                    url, filename=f"{title}.mp3"
                ),
                title=title,
                performer=artist or None,
            )
            if msg.audio and msg.audio.file_id:
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
) -> list[int]:
    new_ids: list[int] = []
    for i, track in enumerate(tracks):
        track_id: int = track["id"]
        title = track.get("title", "Без названия")
        artist = track.get("artist") or track.get(
            "performer", ""
        )

        cached_fid = await get_cached_file_id(
            track_id
        )
        if not cached_fid:
            try:
                cached_fid = (
                    await client.get_stream_url(
                        track_id, token
                    )
                )
            except BackendError:
                logger.warning(
                    "stream_url_failed",
                    track_id=track_id,
                )
                continue

        if i < len(session.audio_message_ids):
            try:
                await bot.edit_message_media(
                    chat_id=session.chat_id,
                    message_id=(
                        session.audio_message_ids[i]
                    ),
                    media=InputMediaAudio(
                        media=cached_fid,
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
                msg = await bot.send_audio(
                    chat_id=session.chat_id,
                    audio=cached_fid,
                    title=title,
                    performer=artist or None,
                )
                msg_id = msg.message_id
                if (
                    msg.audio and msg.audio.file_id
                ):
                    await set_cached_file_id(
                        track_id, msg.audio.file_id
                    )
        else:
            msg = await bot.send_audio(
                chat_id=session.chat_id,
                audio=cached_fid,
                title=title,
                performer=artist or None,
            )
            msg_id = msg.message_id
            if msg.audio and msg.audio.file_id:
                await set_cached_file_id(
                    track_id, msg.audio.file_id
                )

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


@router.callback_query(F.data == "menu:player")
async def on_player_menu(
    callback: CallbackQuery,
) -> None:
    await callback.answer()
    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            "🎧 <b>Плеер</b>\n\n"
            "Выбери источник треков:",
            reply_markup=player_source_kb(),
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
    await callback.answer("Загрузка...")

    source = callback.data.split(":")[-1]
    telegram_id = callback.from_user.id
    chat_id = callback.message.chat.id if callback.message else telegram_id

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
            token_data = (
                await client.get_internal_token(
                    telegram_id,
                    settings.internal_api_secret,
                )
            )
            token = token_data["access_token"]
            user_id: int = token_data["user_id"]
            import time

            _token_cache[telegram_id] = (
                token,
                time.time(),
            )
        except BackendError:
            if callback.message and isinstance(
                callback.message, Message
            ):
                await callback.message.edit_text(
                    "Не удалось авторизоваться. "
                    "Попробуй позже.",
                    reply_markup=main_menu_kb(),
                )
            return

        try:
            tracks, total, has_more = (
                await _fetch_tracks(
                    client,
                    source,
                    telegram_id,
                    token,
                    user_id,
                    page=1,
                )
            )
        except BackendError:
            if callback.message and isinstance(
                callback.message, Message
            ):
                await callback.message.edit_text(
                    "Не удалось загрузить треки. "
                    "Попробуй позже.",
                    reply_markup=main_menu_kb(),
                )
            return

        if not tracks:
            if callback.message and isinstance(
                callback.message, Message
            ):
                await callback.message.edit_text(
                    "Треков не найдено.",
                    reply_markup=main_menu_kb(),
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
        )

    text = format_player_message(
        source, tracks, page=1, total=total
    )
    control_msg = await callback.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        reply_markup=player_control_kb(
            len(msg_ids), has_more
        ),
    )

    session = player_sessions.create(
        chat_id=chat_id,
        user_id=telegram_id,
        source=source,
    )
    session.audio_message_ids = msg_ids
    session.control_message_id = (
        control_msg.message_id
    )
    session.track_ids = [t["id"] for t in tracks]
    session.page = 1
    session.has_more = has_more
    session.touch()


@router.callback_query(F.data == "player:next")
async def on_player_next(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user:
        await callback.answer()
        return

    telegram_id = callback.from_user.id
    session = player_sessions.get(telegram_id)
    if not session:
        await callback.answer(
            "Сессия истекла. Открой плеер заново."
        )
        return

    await callback.answer("Загрузка...")
    session.touch()

    async with BackendClient() as client:
        token = await _get_token(
            client, telegram_id
        )
        try:
            tracks, total, has_more = (
                await _fetch_tracks(
                    client,
                    session.source,
                    telegram_id,
                    token,
                    session.user_id,
                    page=session.page + 1,
                )
            )
        except BackendError:
            await callback.answer(
                "Ошибка загрузки."
            )
            return

        if not tracks:
            await callback.answer(
                "Больше треков нет."
            )
            session.has_more = False
            return

        new_ids = await _edit_audio_batch(
            callback.bot,
            client,
            session,
            tracks,
            token,
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
    )
    try:
        await callback.bot.edit_message_text(
            chat_id=session.chat_id,
            message_id=session.control_message_id,
            text=text,
            parse_mode="HTML",
            reply_markup=player_control_kb(
                len(new_ids), has_more
            ),
        )
    except Exception:
        pass


@router.callback_query(
    F.data.startswith("player:like:")
)
async def on_player_like(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user or not callback.data:
        await callback.answer()
        return

    telegram_id = callback.from_user.id
    session = player_sessions.get(telegram_id)
    if not session:
        await callback.answer(
            "Сессия истекла."
        )
        return

    idx_str = callback.data.split(":")[-1]
    try:
        idx = int(idx_str)
    except ValueError:
        await callback.answer()
        return

    if idx < 0 or idx >= len(session.track_ids):
        await callback.answer("Трек не найден.")
        return

    track_id = session.track_ids[idx]
    session.touch()

    async with BackendClient() as client:
        try:
            token_data = (
                await client.get_internal_token(
                    telegram_id,
                    settings.internal_api_secret,
                )
            )
            user_id = token_data["user_id"]
            result = await client.toggle_like(
                user_id, track_id
            )
            liked = result.get("liked", False)
            await callback.answer(
                "❤️ Лайк!"
                if liked
                else "Лайк убран"
            )
        except BackendError:
            await callback.answer(
                "Ошибка. Попробуй позже."
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
        await callback.message.edit_text(
            f"Привет, <b>{name}</b>! 👋\n\n"
            "Добро пожаловать в <b>.sound</b> — "
            "музыка без рекламы.\n"
            "Слушай. Делись. Открывай.",
            reply_markup=main_menu_kb(),
        )

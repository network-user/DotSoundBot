import structlog
from aiogram import Bot, F, Router
from aiogram.types import Document, Message

from bot.api.client import BackendClient, BackendError
from bot.config import settings
from bot.i18n.core import resolve_lang, tr
from bot.keyboards.inline import track_action_keyboard
from bot.utils.formatting import safe_html

router = Router()
logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_AUDIO_MIMES = frozenset(
    {
        "audio/mpeg",
        "audio/ogg",
        "audio/wav",
        "audio/flac",
        "audio/mp4",
        "audio/x-m4a",
        "audio/aac",
    }
)


def _is_audio_document(doc: Document) -> bool:
    if not doc:
        return False
    mime = doc.mime_type or ""
    return mime.startswith("audio/") or mime in _AUDIO_MIMES


@router.message(F.audio)
async def handle_audio(message: Message, bot: Bot) -> None:
    if not message.audio or not message.from_user:
        return

    audio = message.audio
    user = message.from_user
    lang = resolve_lang(user.language_code)

    structlog.contextvars.bind_contextvars(
        handler="handle_audio",
        user_id=user.id,
        file_id=audio.file_id,
        duration=audio.duration,
    )
    logger.info("audio_upload_received")

    title = (
        audio.title
        or audio.file_name
        or "Unknown Track"
    )
    artist = audio.performer

    file_info = await bot.get_file(audio.file_id)
    file_bytes = await bot.download_file(
        file_info.file_path or ""
    )
    if file_bytes is None:
        logger.error("audio_download_failed")
        await message.reply(
            tr("audio.download_failed", lang)
        )
        return

    data = file_bytes.read()

    async with BackendClient() as client:
        try:
            track = await client.upload_audio(
                file_bytes=data,
                filename=audio.file_name or "track.mp3",
                content_type=audio.mime_type or "audio/mpeg",
                title=title,
                artist=artist,
                uploader_id=user.id,
            )
            track_id = track["id"]
            logger.info(
                "audio_upload_success",
                track_id=track_id,
                title=title,
            )
            mini_app_url = (
                f"{settings.mini_app_url}"
                f"?track_id={track_id}"
            )
            safe_title = safe_html(title, 80)
            safe_artist = safe_html(artist, 60)
            artist_line = (
                f"\n👤 {safe_artist}"
                if safe_artist
                else ""
            )
            await message.reply(
                tr("audio.uploaded", lang)
                + f"🎵 <b>{safe_title}</b>"
                + artist_line,
                parse_mode="HTML",
                reply_markup=track_action_keyboard(
                    track_id, mini_app_url, lang
                ),
            )
        except BackendError as exc:
            logger.error(
                "audio_upload_failed",
                status=exc.status_code,
                detail=exc.detail,
            )
            await message.reply(
                tr("audio.upload_error", lang)
            )


@router.message(F.document.func(_is_audio_document))  # type: ignore[arg-type]
async def handle_audio_document(
    message: Message, bot: Bot
) -> None:
    if not message.document or not message.from_user:
        return

    doc = message.document
    user = message.from_user
    lang = resolve_lang(user.language_code)

    structlog.contextvars.bind_contextvars(
        handler="handle_audio_document",
        user_id=user.id,
        file_id=doc.file_id,
    )
    logger.info("audio_document_received")

    title = doc.file_name or "Unknown Track"
    file_info = await bot.get_file(doc.file_id)
    file_bytes = await bot.download_file(
        file_info.file_path or ""
    )
    if file_bytes is None:
        await message.reply(
            tr("audio.reply_download", lang)
        )
        return

    data = file_bytes.read()

    async with BackendClient() as client:
        try:
            track = await client.upload_audio(
                file_bytes=data,
                filename=doc.file_name or "track.mp3",
                content_type=doc.mime_type or "audio/mpeg",
                title=title,
                uploader_id=user.id,
            )
            track_id = track["id"]
            logger.info(
                "audio_document_upload_success",
                track_id=track_id,
            )
            mini_app_url = (
                f"{settings.mini_app_url}"
                f"?track_id={track_id}"
            )
            safe_title = safe_html(title, 80)
            await message.reply(
                tr("audio.uploaded_doc", lang)
                + f"{safe_title}</b>",
                parse_mode="HTML",
                reply_markup=track_action_keyboard(
                    track_id, mini_app_url, lang
                ),
            )
        except BackendError as exc:
            logger.error(
                "audio_document_upload_failed",
                status=exc.status_code,
            )
            await message.reply(
                tr("audio.format_error", lang)
            )

import structlog
from aiogram import Bot, F, Router
from aiogram.types import Message

from bot.api.client import BackendClient, BackendError
from bot.config import settings
from bot.keyboards.inline import open_player_keyboard

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


def _is_audio_document(message: Message) -> bool:
    doc = message.document
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
            "Не удалось скачать файл. Попробуй ещё раз."
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
                f"{settings.backend_base_url}/mini_app/"
                f"?track_id={track_id}"
            )
            await message.reply(
                f"✅ Трек загружен!\n\n"
                f"🎵 <b>{title}</b>"
                + (f"\n👤 {artist}" if artist else ""),
                parse_mode="HTML",
                reply_markup=open_player_keyboard(mini_app_url),
            )
        except BackendError as exc:
            logger.error(
                "audio_upload_failed",
                status=exc.status_code,
                detail=exc.detail,
            )
            await message.reply(
                "Ошибка при загрузке трека. "
                "Поддерживаемые форматы: MP3, OGG, WAV, FLAC, M4A."
            )


@router.message(F.document.func(_is_audio_document))  # type: ignore[arg-type]
async def handle_audio_document(
    message: Message, bot: Bot
) -> None:
    if not message.document or not message.from_user:
        return

    doc = message.document
    user = message.from_user

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
        await message.reply("Не удалось скачать файл.")
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
                f"{settings.backend_base_url}/mini_app/"
                f"?track_id={track_id}"
            )
            await message.reply(
                f"✅ Трек загружен!\n🎵 <b>{title}</b>",
                parse_mode="HTML",
                reply_markup=open_player_keyboard(mini_app_url),
            )
        except BackendError as exc:
            logger.error(
                "audio_document_upload_failed",
                status=exc.status_code,
            )
            await message.reply(
                "Ошибка при загрузке. Убедись, что файл "
                "является аудио в поддерживаемом формате."
            )

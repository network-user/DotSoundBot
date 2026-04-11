import io
from typing import Any

import structlog
from aiohttp import web
from aiogram import Bot

from bot.config import settings

logger: structlog.stdlib.BoundLogger = structlog.get_logger(
    __name__
)

_MAX_DOWNLOAD_SIZE = 20 * 1024 * 1024


def _check_secret(request: web.Request) -> bool:
    expected = settings.internal_api_secret
    if not expected:
        return True
    token = request.headers.get("X-Internal-Secret", "")
    ok = token == expected
    if not ok:
        logger.warning(
            "internal_auth_failed",
            expected_len=len(expected),
            received_len=len(token),
            match=ok,
        )
    return ok


async def handle_profile_audios(
    request: web.Request,
) -> web.Response:
    if not _check_secret(request):
        return web.json_response(
            {"error": "forbidden"}, status=403
        )

    user_id = int(request.match_info["user_id"])
    bot: Bot = request.app["bot"]

    try:
        result = await bot.get_user_profile_audios(
            user_id=user_id, limit=100
        )
    except Exception as exc:
        logger.error(
            "profile_audios_failed",
            user_id=user_id,
            error=str(exc),
        )
        return web.json_response(
            {"error": str(exc)}, status=500
        )

    audios: list[dict[str, Any]] = []
    for audio in result.audios:
        audios.append(
            {
                "file_id": audio.file_id,
                "file_unique_id": audio.file_unique_id,
                "title": audio.title or "Unknown",
                "performer": audio.performer,
                "duration": audio.duration,
                "file_size": audio.file_size,
                "mime_type": audio.mime_type,
            }
        )

    logger.info(
        "profile_audios_fetched",
        user_id=user_id,
        count=len(audios),
    )
    return web.json_response(
        {
            "total_count": result.total_count,
            "audios": audios,
        }
    )


async def handle_download_audio(
    request: web.Request,
) -> web.Response:
    if not _check_secret(request):
        return web.json_response(
            {"error": "forbidden"}, status=403
        )

    body = await request.json()
    file_id: str = body.get("file_id", "")
    if not file_id:
        return web.json_response(
            {"error": "file_id required"}, status=400
        )

    bot: Bot = request.app["bot"]

    try:
        file = await bot.get_file(file_id)
        if not file.file_path:
            return web.json_response(
                {"error": "file_path missing"}, status=404
            )
        if (
            file.file_size
            and file.file_size > _MAX_DOWNLOAD_SIZE
        ):
            return web.json_response(
                {"error": "file_too_large"}, status=413
            )

        buf = io.BytesIO()
        await bot.download_file(file.file_path, buf)
        data = buf.getvalue()

        logger.info(
            "audio_downloaded",
            file_id=file_id[:20],
            size=len(data),
        )
        return web.Response(
            body=data,
            content_type="audio/mpeg",
            headers={
                "Content-Length": str(len(data)),
            },
        )
    except Exception as exc:
        logger.error(
            "audio_download_failed",
            file_id=file_id[:20],
            error=str(exc),
        )
        return web.json_response(
            {"error": str(exc)}, status=500
        )


def create_internal_app(bot: Bot) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.router.add_get(
        "/internal/profile-audios/{user_id}",
        handle_profile_audios,
    )
    app.router.add_post(
        "/internal/download-audio",
        handle_download_audio,
    )
    return app

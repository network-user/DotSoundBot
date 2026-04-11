import io
from typing import Any

import structlog
from aiohttp import web
from aiogram import Bot

from bot.config import settings

logger: structlog.stdlib.BoundLogger = (
    structlog.get_logger(__name__)
)

_MAX_DOWNLOAD_SIZE = 20 * 1024 * 1024


def _check_secret(request: web.Request) -> bool:
    expected = settings.internal_api_secret
    if not expected:
        return True
    token = request.headers.get(
        "X-Internal-Secret", ""
    )
    ok = token == expected
    if not ok:
        logger.warning(
            "internal_auth_failed",
            expected_len=len(expected),
            received_len=len(token),
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
        result = (
            await bot.get_user_profile_audios(
                user_id=user_id, limit=100
            )
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
                {"error": "file_path missing"},
                status=404,
            )
        if (
            file.file_size
            and file.file_size > _MAX_DOWNLOAD_SIZE
        ):
            return web.json_response(
                {"error": "file_too_large"},
                status=413,
            )

        buf = io.BytesIO()
        await bot.download_file(
            file.file_path, buf
        )
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


async def handle_send_auth_code(
    request: web.Request,
) -> web.Response:
    if not _check_secret(request):
        return web.json_response(
            {"error": "forbidden"}, status=403
        )

    body = await request.json()
    telegram_id: int = body.get("telegram_id", 0)
    code: str = body.get("code", "")

    if not telegram_id or not code:
        return web.json_response(
            {"error": "telegram_id and code required"},
            status=400,
        )

    bot: Bot = request.app["bot"]

    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                f"🔐 <b>Код входа в .sound</b>\n\n"
                f"<code>{code}</code>\n\n"
                f"Действует 5 минут. "
                f"Никому не сообщайте этот код."
            ),
            parse_mode="HTML",
        )
        logger.info(
            "auth_code_sent",
            telegram_id=telegram_id,
        )
        return web.json_response({"sent": True})
    except Exception as exc:
        logger.error(
            "auth_code_send_failed",
            telegram_id=telegram_id,
            error=str(exc),
        )
        return web.json_response(
            {"error": str(exc)}, status=500
        )


async def handle_send_login_notification(
    request: web.Request,
) -> web.Response:
    if not _check_secret(request):
        return web.json_response(
            {"error": "forbidden"}, status=403
        )

    body = await request.json()
    telegram_id: int = body.get("telegram_id", 0)
    ip: str = body.get("ip", "unknown")
    device: str = body.get("device", "unknown")
    time_str: str = body.get("time", "unknown")

    if not telegram_id:
        return web.json_response(
            {"error": "telegram_id required"},
            status=400,
        )

    bot: Bot = request.app["bot"]

    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                "✅ <b>Выполнен вход в .sound web"
                "</b>\n\n"
                f"🕐 Время: {time_str}\n"
                f"🌐 IP: {ip}\n"
                f"📱 Устройство: {device}\n\n"
                "<i>Если это были не вы, "
                "немедленно смените пароль "
                "или свяжитесь с поддержкой."
                "</i>"
            ),
            parse_mode="HTML",
        )
        logger.info(
            "login_notification_sent",
            telegram_id=telegram_id,
        )
        return web.json_response({"sent": True})
    except Exception as exc:
        logger.error(
            "login_notification_failed",
            telegram_id=telegram_id,
            error=str(exc),
        )
        return web.json_response(
            {"error": str(exc)}, status=500
        )


def create_internal_app(
    bot: Bot,
) -> web.Application:
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
    app.router.add_post(
        "/internal/send-auth-code",
        handle_send_auth_code,
    )
    app.router.add_post(
        "/internal/send-login-notification",
        handle_send_login_notification,
    )
    return app

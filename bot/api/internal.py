import io
from typing import Any

import structlog
from aiogram import Bot
from aiohttp import web
from dotsound_private_core.contracts import (
    ADMIN_ALERT_ENDPOINT,
    DOWNLOAD_AUDIO_ENDPOINT,
    INTERNAL_SECRET_HEADER,
    PROFILE_AUDIOS_ENDPOINT_TEMPLATE,
    SEND_AUTH_CODE_ENDPOINT,
    SEND_LOGIN_NOTIFICATION_ENDPOINT,
)

from bot.config import settings
from bot.utils.formatting import html_escape

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_MAX_DOWNLOAD_SIZE = 20 * 1024 * 1024
_ALLOWED_ALERT_SEVERITIES = frozenset({"info", "warning", "critical"})
_SEVERITY_PREFIX = {
    "info": "ℹ️",
    "warning": "⚠️",
    "critical": "🚨",
}
_MAX_ALERT_TITLE = 200
_MAX_ALERT_DETAILS = 1500


def _error_response(code: str, status: int) -> web.Response:
    """Generic error response without leaking exception text."""
    return web.json_response({"error": code}, status=status)


def _allowed_admin_chat_ids() -> set[str]:
    raw = settings.admin_alert_chat_id_allowlist or ""
    return {item.strip() for item in raw.split(",") if item.strip()}


def _check_secret(request: web.Request) -> bool:
    expected = settings.internal_api_secret
    if not expected:
        logger.error("internal_api_secret_not_configured")
        return False
    token = request.headers.get(INTERNAL_SECRET_HEADER, "")
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
        return web.json_response({"error": "forbidden"}, status=403)

    user_id = int(request.match_info["user_id"])
    bot: Bot = request.app["bot"]

    try:
        result = await bot.get_user_profile_audios(user_id=user_id, limit=100)
    except Exception:
        logger.exception(
            "profile_audios_failed",
            user_id=user_id,
        )
        return _error_response("profile_audios_failed", 500)

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
        return web.json_response({"error": "forbidden"}, status=403)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
    file_id: str = body.get("file_id", "")
    if not file_id:
        return web.json_response({"error": "file_id required"}, status=400)

    bot: Bot = request.app["bot"]

    try:
        file = await bot.get_file(file_id)
        if not file.file_path:
            return web.json_response(
                {"error": "file_path missing"},
                status=404,
            )
        if file.file_size and file.file_size > _MAX_DOWNLOAD_SIZE:
            return web.json_response(
                {"error": "file_too_large"},
                status=413,
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
    except Exception:
        logger.exception(
            "audio_download_failed",
            file_id=file_id[:20],
        )
        return _error_response("audio_download_failed", 500)


async def handle_send_auth_code(
    request: web.Request,
) -> web.Response:
    if not _check_secret(request):
        return web.json_response({"error": "forbidden"}, status=403)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
    telegram_id: int = body.get("telegram_id", 0)
    code: str = body.get("code", "")

    if not telegram_id or not code:
        return web.json_response(
            {"error": "telegram_id and code required"},
            status=400,
        )

    bot: Bot = request.app["bot"]

    safe_code = html_escape(code)
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                f"🔐 <b>Код входа в .sound</b>\n\n"
                f"<code>{safe_code}</code>\n\n"
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
    except Exception:
        logger.exception(
            "auth_code_send_failed",
            telegram_id=telegram_id,
        )
        return _error_response("auth_code_send_failed", 500)


async def handle_send_login_notification(
    request: web.Request,
) -> web.Response:
    if not _check_secret(request):
        return web.json_response({"error": "forbidden"}, status=403)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
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

    from aiogram.types import (
        InlineKeyboardButton,
        InlineKeyboardMarkup,
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="menu:player",
                )
            ]
        ]
    )

    safe_time = html_escape(time_str)
    safe_ip = html_escape(ip)
    safe_device = html_escape(device)
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                "✅ <b>Выполнен вход в .sound web"
                "</b>\n\n"
                f"🕐 Время: {safe_time}\n"
                f"🌐 IP: {safe_ip}\n"
                f"📱 Устройство: {safe_device}\n\n"
                "<i>Если это были не вы, "
                "немедленно смените пароль "
                "или свяжитесь с поддержкой."
                "</i>"
            ),
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        logger.info(
            "login_notification_sent",
            telegram_id=telegram_id,
        )
        return web.json_response({"sent": True})
    except Exception:
        logger.exception(
            "login_notification_failed",
            telegram_id=telegram_id,
        )
        return _error_response("login_notification_failed", 500)


async def handle_admin_alert(
    request: web.Request,
) -> web.Response:
    """Forward an admin-panel alert from backend to Telegram.

    The contract is documented in
    ``DotSoundBackend/docs/admin/security.md``::

        POST /internal/admin-alert
        Headers: X-Internal-Secret: {bot_internal_secret}
        Body:
          {
            "chat_id":   str,
            "event_type": str,
            "severity":  "info" | "warning" | "critical",
            "title":     str,
            "details":   str,
            "user_id":   int | null,
            "ip":        str | null,
            "ua":        str | null,
            "ts":        ISO8601
          }
    """
    if not _check_secret(request):
        return web.json_response({"error": "forbidden"}, status=403)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
    if not isinstance(body, dict):
        return web.json_response(
            {"error": "object expected"},
            status=400,
        )

    chat_id_raw = body.get("chat_id")
    event_type = str(body.get("event_type", "")).strip()
    severity = str(body.get("severity", "info")).strip()
    title = str(body.get("title", "")).strip()
    details = str(body.get("details", "")).strip()
    user_id = body.get("user_id")
    ip = body.get("ip")
    ua = body.get("ua")
    ts = body.get("ts")

    if not chat_id_raw or not event_type or not title:
        return web.json_response(
            {"error": ("chat_id, event_type, " "title are required")},
            status=400,
        )
    if severity not in _ALLOWED_ALERT_SEVERITIES:
        return web.json_response(
            {"error": "unknown severity"},
            status=400,
        )

    chat_id = str(chat_id_raw).strip()
    allowlist = _allowed_admin_chat_ids()
    if allowlist and chat_id not in allowlist:
        logger.warning(
            "admin_alert_chat_not_allowed",
            chat_id=chat_id,
        )
        return web.json_response(
            {"error": "chat_id not allowed"},
            status=403,
        )

    if len(title) > _MAX_ALERT_TITLE:
        title = title[: _MAX_ALERT_TITLE - 1] + "…"
    if len(details) > _MAX_ALERT_DETAILS:
        details = details[: _MAX_ALERT_DETAILS - 1] + "…"

    bot: Bot = request.app["bot"]
    safe_title = html_escape(title)
    safe_details = html_escape(details)
    prefix = _SEVERITY_PREFIX.get(severity, _SEVERITY_PREFIX["info"])
    safe_event = html_escape(event_type)
    safe_severity = html_escape(severity.upper())
    lines = [
        f"{prefix} <b>{safe_title}</b>",
        (f"<i>{safe_severity} · " f"<code>{safe_event}</code></i>"),
    ]
    if safe_details:
        lines.append("")
        lines.append(safe_details)
    meta_parts = []
    if user_id is not None:
        meta_parts.append(f"user_id=<code>{html_escape(str(user_id))}</code>")
    if ip:
        meta_parts.append(f"ip=<code>{html_escape(str(ip))}</code>")
    if ua:
        meta_parts.append(f"ua=<code>{html_escape(str(ua)[:80])}</code>")
    if ts:
        meta_parts.append(f"at=<code>{html_escape(str(ts))}</code>")
    if meta_parts:
        lines.append("")
        lines.append(" · ".join(meta_parts))
    text = "\n".join(lines)

    try:
        chat_id_value: int | str
        try:
            chat_id_value = int(chat_id)
        except ValueError:
            chat_id_value = chat_id
        await bot.send_message(
            chat_id=chat_id_value,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        logger.info(
            "admin_alert_delivered",
            event_type=event_type,
            severity=severity,
            chat_id=chat_id,
        )
        return web.json_response({"sent": True})
    except Exception:
        logger.exception(
            "admin_alert_send_failed",
            event_type=event_type,
            severity=severity,
            chat_id=chat_id,
        )
        return _error_response("admin_alert_send_failed", 500)


def create_internal_app(
    bot: Bot,
) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.router.add_get(
        PROFILE_AUDIOS_ENDPOINT_TEMPLATE,
        handle_profile_audios,
    )
    app.router.add_post(
        DOWNLOAD_AUDIO_ENDPOINT,
        handle_download_audio,
    )
    app.router.add_post(
        SEND_AUTH_CODE_ENDPOINT,
        handle_send_auth_code,
    )
    app.router.add_post(
        SEND_LOGIN_NOTIFICATION_ENDPOINT,
        handle_send_login_notification,
    )
    app.router.add_post(
        ADMIN_ALERT_ENDPOINT,
        handle_admin_alert,
    )
    return app

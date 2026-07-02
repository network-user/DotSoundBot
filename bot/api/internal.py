import asyncio
import hmac
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
    SEND_REMOTE_BACKUP_NOTIFICATION_ENDPOINT,
    SEND_AUTH_CODE_ENDPOINT,
    SEND_LOGIN_NOTIFICATION_ENDPOINT,
    is_remote_backup_status,
)

from bot.config import settings
from bot.i18n.core import resolve_lang, tr
from bot.utils.formatting import html_escape

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_MAX_DOWNLOAD_SIZE = 20 * 1024 * 1024
# Каждое скачивание держит файл (до 20 МБ) в RAM целиком; без
# ограничения параллельные запросы бэкенда множат этот буфер.
_DOWNLOAD_SEMAPHORE = asyncio.Semaphore(2)
_ALLOWED_ALERT_SEVERITIES = frozenset({"info", "warning", "critical"})
_SEVERITY_PREFIX = {
    "info": "ℹ️",
    "warning": "⚠️",
    "critical": "🚨",
}
_MAX_ALERT_TITLE = 200
_MAX_ALERT_DETAILS = 1500
_MAX_BACKUP_REASON = 600
_BACKUP_PREFIX = {
    "started": "🟦",
    "success": "🟩",
    "failed": "🟥",
}


def _mask_user_id(value: Any) -> str:
    try:
        s = str(int(value))
    except (TypeError, ValueError):
        return "***"
    if len(s) <= 4:
        return "*" * len(s)
    return f"{s[:2]}***{s[-2:]}"


def _mask_ip(value: str) -> str:
    v = value.strip()
    if ":" in v:
        parts = v.split(":")
        return ":".join(parts[:2] + ["…"] if len(parts) > 2 else parts)
    parts = v.split(".")
    if len(parts) == 4:
        return ".".join(parts[:2] + ["x", "x"])
    return "***"


async def handle_health(
    request: web.Request,
) -> web.Response:
    return web.json_response({"status": "ok"})


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
    ok = hmac.compare_digest(token, expected)
    if not ok:
        logger.warning("internal_auth_failed")
    return ok


async def handle_profile_audios(
    request: web.Request,
) -> web.Response:
    if not _check_secret(request):
        return web.json_response({"error": "forbidden"}, status=403)

    try:
        user_id = int(request.match_info["user_id"])
    except (KeyError, ValueError):
        return web.json_response(
            {"error": "invalid user_id"}, status=400
        )
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
        async with _DOWNLOAD_SEMAPHORE:
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
            await bot.download_file(file.file_path, buf)
            # getbuffer() — zero-copy memoryview поверх BytesIO;
            # getvalue() делал вторую полную копию файла.
            data = buf.getbuffer()
            size = data.nbytes

            logger.info(
                "audio_downloaded",
                file_id=file_id[:20],
                size=size,
            )
            return web.Response(
                body=data,
                content_type="audio/mpeg",
                headers={
                    "Content-Length": str(size),
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
    lang = resolve_lang(
        str(body.get("language_code", "")) or None
    )

    safe_code = html_escape(code)
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=tr("internal.code_message", lang).format(
                code=safe_code
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
    lang = resolve_lang(
        str(body.get("language_code", "")) or None
    )

    from aiogram.types import (
        InlineKeyboardButton,
        InlineKeyboardMarkup,
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=tr("internal.open_player", lang),
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
            text=tr("internal.login_notice", lang).format(
                time=safe_time,
                ip=safe_ip,
                device=safe_device,
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

    The route and the internal secret header are defined by
    ``dotsound_private_core.contracts`` (``ADMIN_ALERT_ENDPOINT`` /
    ``INTERNAL_SECRET_HEADER``); the full contract is documented in
    ``DotSoundBackend/docs/admin/security.md``. Request body::

        {
            "chat_id":    str,
            "event_type": str,
            "severity":   "info" | "warning" | "critical",
            "title":      str,
            "details":    str,
            "user_id":    int | null,
            "ip":         str | null,
            "ua":         str | null,
            "ts":         ISO8601
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
    prefix = _SEVERITY_PREFIX.get(severity, _SEVERITY_PREFIX["info"])
    lines = [
        f"{prefix} {title}",
        f"{severity.upper()} · {event_type}",
    ]
    if details:
        lines.append("")
        lines.append(details)
    meta_parts = []
    if user_id is not None:
        meta_parts.append(f"user={_mask_user_id(user_id)}")
    if ip:
        meta_parts.append(f"ip={_mask_ip(str(ip))}")
    if ua:
        meta_parts.append(f"ua={str(ua)[:80]}")
    if ts:
        meta_parts.append(f"at={ts}")
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
            parse_mode=None,
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


async def handle_send_remote_backup_notification(
    request: web.Request,
) -> web.Response:
    if not _check_secret(request):
        return web.json_response({"error": "forbidden"}, status=403)

    notify_chat_id = settings.backup_notify_telegram_id
    if not notify_chat_id:
        return _error_response(
            "backup_notify_chat_not_configured", 503
        )

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
    if not isinstance(body, dict):
        return web.json_response(
            {"error": "object expected"},
            status=400,
        )

    user_id_raw = body.get("user_id", 0)
    backup_id = str(body.get("backup_id", "")).strip()
    status_value = str(body.get("status", "")).strip()
    timestamp_ms = body.get("timestamp_ms", 0)
    reason_raw = body.get("reason")

    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        user_id = 0
    try:
        ts_ms = int(timestamp_ms)
    except (TypeError, ValueError):
        ts_ms = 0

    if user_id <= 0 or not backup_id or ts_ms <= 0:
        return web.json_response(
            {
                "error": (
                    "user_id, backup_id, timestamp_ms are required"
                )
            },
            status=400,
        )
    if not is_remote_backup_status(status_value):
        return web.json_response(
            {"error": "unknown status"},
            status=400,
        )

    reason = ""
    if reason_raw is not None:
        reason = str(reason_raw).strip()
    if len(reason) > _MAX_BACKUP_REASON:
        reason = reason[: _MAX_BACKUP_REASON - 1] + "…"

    safe_backup_id = html_escape(backup_id)
    safe_status = html_escape(status_value.upper())
    safe_user_id = html_escape(str(user_id))
    safe_ts = html_escape(str(ts_ms))
    prefix = _BACKUP_PREFIX.get(status_value, "ℹ️")

    lines = [
        f"{prefix} <b>Remote backup {safe_status}</b>",
        f"user_id=<code>{safe_user_id}</code>",
        f"backup_id=<code>{safe_backup_id}</code>",
        f"timestamp_ms=<code>{safe_ts}</code>",
    ]
    if reason:
        lines.append(f"reason: {html_escape(reason)}")
    text = "\n".join(lines)

    bot: Bot = request.app["bot"]
    try:
        await bot.send_message(
            chat_id=notify_chat_id,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        logger.info(
            "remote_backup_notification_sent",
            user_id=user_id,
            backup_id=backup_id,
            status=status_value,
            chat_id=notify_chat_id,
        )
        return web.json_response({"sent": True})
    except Exception:
        logger.exception(
            "remote_backup_notification_send_failed",
            user_id=user_id,
            backup_id=backup_id,
            status=status_value,
            chat_id=notify_chat_id,
        )
        return _error_response(
            "remote_backup_notification_send_failed", 500
        )


def create_internal_app(
    bot: Bot,
) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.router.add_get("/health", handle_health)
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
    app.router.add_post(
        SEND_REMOTE_BACKUP_NOTIFICATION_ENDPOINT,
        handle_send_remote_backup_notification,
    )
    return app

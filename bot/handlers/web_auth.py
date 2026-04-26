import structlog
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotsound_private_core.services import (
    auth_generate_code_url,
    build_internal_headers,
)

from bot.config import settings
from bot.i18n.core import resolve_lang, tr
from bot.utils.formatting import html_escape

router = Router(name="web_auth")
logger: structlog.stdlib.BoundLogger = (
    structlog.get_logger(__name__)
)

@router.message(
    CommandStart(
        deep_link=True,
        deep_link_encoded=False,
    ),
    lambda m: (m.text or "").endswith("web_login"),
)
async def cmd_start_web_login(
    message: Message,
) -> None:
    if not message.from_user:
        return

    user = message.from_user
    lang = resolve_lang(user.language_code)
    structlog.contextvars.bind_contextvars(
        telegram_id=user.id,
        handler="web_login",
    )
    logger.info("web_login_requested")

    import httpx

    try:
        async with httpx.AsyncClient(
            timeout=10,
        ) as client:
            resp = await client.post(
                auth_generate_code_url(
                    settings.backend_base_url
                ),
                headers=build_internal_headers(
                    settings.internal_api_secret
                ),
                json={"telegram_id": user.id},
            )
            if resp.status_code != 200:
                raise Exception(
                    f"Backend returned "
                    f"{resp.status_code}"
                )
            data = resp.json()
            code = data["code"]
    except Exception as exc:
        logger.error(
            "web_login_code_failed",
            error=str(exc),
        )
        await message.answer(
            tr("webauth.code_error", lang),
        )
        return

    site_url = settings.mini_app_url.rstrip("/")
    auth_url = f"{site_url}?auth=code"
    buttons = [
        [
            InlineKeyboardButton(
                text=tr("webauth.open_site", lang),
                url=auth_url,
            )
        ],
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    safe = html_escape(code)
    await message.answer(
        tr("webauth.message", lang).format(
            code=safe
        ),
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    logger.info(
        "web_login_code_sent",
        telegram_id=user.id,
    )

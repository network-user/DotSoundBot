import structlog
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.api.client import BackendClient
from bot.config import settings

router = Router(name="web_auth")
logger: structlog.stdlib.BoundLogger = (
    structlog.get_logger(__name__)
)

_BACKEND_GENERATE_URL = (
    "/api/v1/auth/generate-code"
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
    structlog.contextvars.bind_contextvars(
        telegram_id=user.id,
        handler="web_login",
    )
    logger.info("web_login_requested")

    import httpx

    headers: dict[str, str] = {}
    if settings.internal_api_secret:
        headers["X-Internal-Secret"] = (
            settings.internal_api_secret
        )

    try:
        async with httpx.AsyncClient(
            base_url=settings.backend_base_url,
            timeout=10,
        ) as client:
            resp = await client.post(
                _BACKEND_GENERATE_URL,
                headers=headers,
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
            "Не удалось сгенерировать код. "
            "Попробуйте позже.",
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Вернуться в профиль",
                    callback_data="profile",
                )
            ]
        ]
    )

    await message.answer(
        f"🔐 <b>Код входа в .sound</b>\n\n"
        f"<code>{code}</code>\n\n"
        f"⏱ Действует <b>5 минут</b>\n\n"
        f"<i>Введите этот код на сайте</i>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    logger.info(
        "web_login_code_sent",
        telegram_id=user.id,
    )

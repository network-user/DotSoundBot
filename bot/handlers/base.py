import structlog
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.api.client import BackendClient, BackendError
from bot.i18n.core import resolve_lang, tr
from bot.keyboards.inline import (
    about_kb,
    back_to_about_kb,
    back_to_menu_kb,
    help_keyboard,
    main_menu_kb,
    playlists_keyboard,
    profile_kb,
)
from bot.utils.formatting import (
    format_main_menu_welcome,
    html_escape,
    safe_html,
)

router = Router()
logger: structlog.stdlib.BoundLogger = (
    structlog.get_logger(__name__)
)

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not message.from_user:
        return

    user = message.from_user
    structlog.contextvars.bind_contextvars(
        telegram_id=user.id,
        handler="cmd_start",
    )
    logger.info("cmd_start_called")

    lang = resolve_lang(user.language_code)
    await message.answer(
        format_main_menu_welcome(
            user.first_name, lang
        ),
        reply_markup=main_menu_kb(lang),
    )

    try:
        async with BackendClient() as client:
            await client.post(
                "/api/v1/users",
                json={
                    "telegram_id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            )
    except Exception as exc:
        logger.error(
            "backend_registration_failed",
            error=str(exc),
        )


@router.callback_query(F.data == "menu:main")
async def on_main_menu(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    await callback.answer()
    name = callback.from_user.first_name
    lang = resolve_lang(callback.from_user.language_code)
    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            format_main_menu_welcome(name, lang),
            reply_markup=main_menu_kb(lang),
        )


@router.callback_query(F.data == "menu:about")
async def on_about(
    callback: CallbackQuery,
) -> None:
    await callback.answer()
    if not callback.from_user:
        return
    lang = resolve_lang(callback.from_user.language_code)
    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            tr("base.about.title", lang),
            reply_markup=about_kb(lang),
        )


@router.callback_query(
    F.data.startswith("about:")
)
async def on_about_section(
    callback: CallbackQuery,
) -> None:
    if not callback.data:
        await callback.answer()
        return
    section = callback.data.split(":")[1]
    if not callback.from_user:
        await callback.answer()
        return
    lang = resolve_lang(callback.from_user.language_code)
    key = f"base.about.{section}"
    text = tr(key, lang)
    if text == key:
        await callback.answer(
            tr("base.section_missing", lang),
        )
        return
    await callback.answer()
    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            text,
            reply_markup=back_to_about_kb(lang),
        )


@router.callback_query(F.data == "menu:profile")
async def on_profile(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    await callback.answer()
    user = callback.from_user
    lang = resolve_lang(user.language_code)

    async with BackendClient() as client:
        try:
            profile = (
                await client.get_user_profile(user.id)
            )
            stats = await client.get_user_stats(
                profile["id"]
            )
            display_name = (
                (profile.get("first_name") or "")
                + " "
                + (profile.get("last_name") or "")
            ).strip() or (user.first_name or "")
            safe_name = html_escape(display_name)
            username = profile.get("username")
            username_str = (
                f"@{html_escape(username)}\n"
                if username
                else ""
            )
            text = (
                f"<b>{safe_name}</b>\n"
                f"{username_str}\n"
                f"{tr('base.stats.tracks', lang)} "
                f"<b>{stats.get('total_tracks', 0)}"
                f"</b>\n"
                f"{tr('base.stats.plays', lang)} "
                f"<b>{stats.get('total_plays', 0)}"
                f"</b>\n"
                f"{tr('base.stats.likes', lang)} "
                f"<b>{stats.get('total_likes', 0)}"
                f"</b>\n"
                f"{tr('base.stats.followers', lang)} "
                f"<b>{stats.get('followers_count', 0)}</b>"
            )
        except BackendError:
            text = tr("base.profile.load_error", lang)

    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            text,
            reply_markup=profile_kb(lang),
        )

@router.callback_query(
    F.data == "menu:login_history"
)
async def on_login_history(
    callback: CallbackQuery,
) -> None:
    if not callback.from_user:
        await callback.answer()
        return
    await callback.answer()
    user = callback.from_user
    lang = resolve_lang(user.language_code)

    async with BackendClient() as client:
        try:
            profile = (
                await client.get_user_profile(user.id)
            )
            history = (
                await client.get_login_history(
                    profile["id"]
                )
            )
            if not history:
                text = tr("base.login.empty", lang)
            else:
                lines = [tr("base.login.header", lang)]
                for i, entry in enumerate(
                    history, 1
                ):
                    dt = html_escape(
                        entry.get(
                            "created_at", ""
                        )[:16].replace("T", ", ")
                    )
                    device = html_escape(
                        entry.get("device", "—")
                    )
                    ip = html_escape(
                        entry.get("ip", "—")
                    )
                    lines.append(
                        f"{i}. {dt} - "
                        f"{device} - {ip}"
                    )
                lines.append(
                    tr("base.login.footer", lang)
                )
                text = "\n".join(lines)
        except BackendError:
            text = tr("base.login.load_error", lang)

    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            text,
            reply_markup=back_to_menu_kb(lang),
        )


@router.message(F.text == "/help")
async def cmd_help(message: Message) -> None:
    structlog.contextvars.bind_contextvars(
        handler="cmd_help"
    )
    if not message.from_user:
        return
    lang = resolve_lang(message.from_user.language_code)
    await message.answer(
        tr("base.help", lang),
        parse_mode="HTML",
        reply_markup=help_keyboard(lang),
    )


@router.message(F.text == "/profile")
async def cmd_profile(message: Message) -> None:
    if not message.from_user:
        return
    user = message.from_user
    lang = resolve_lang(user.language_code)

    async with BackendClient() as client:
        try:
            profile = (
                await client.get_user_profile(user.id)
            )
            stats = await client.get_user_stats(
                profile["id"]
            )
            display_name = (
                (profile.get("first_name") or "")
                + " "
                + (profile.get("last_name") or "")
            ).strip() or (user.first_name or "")
            safe_name = html_escape(display_name)
            await message.answer(
                f"<b>{safe_name}</b>\n\n"
                f"{tr('base.stats.tracks', lang)} "
                f"<b>{stats.get('total_tracks', 0)}"
                f"</b>\n"
                f"{tr('base.stats.plays', lang)} "
                f"<b>{stats.get('total_plays', 0)}"
                f"</b>\n"
                f"{tr('base.stats.likes', lang)} "
                f"<b>{stats.get('total_likes', 0)}"
                f"</b>",
                parse_mode="HTML",
                reply_markup=profile_kb(lang),
            )
        except BackendError:
            await message.answer(
                tr("base.cmd_profile.error", lang)
            )

@router.message(F.text == "/playlists")
async def cmd_playlists(
    message: Message,
) -> None:
    if not message.from_user:
        return
    user = message.from_user
    lang = resolve_lang(user.language_code)

    async with BackendClient() as client:
        try:
            pls = (
                await client.get_user_playlists(
                    user.id
                )
            )
            if not pls:
                await message.answer(
                    tr("base.playlists.empty", lang),
                    reply_markup=main_menu_kb(lang),
                )
                return
            names = "\n".join(
                f"- <b>{safe_html(pl.get('name'), 60)}</b>"
                for pl in pls[:10]
            )
            await message.answer(
                tr("base.playlists.caption", lang).format(
                    n=len(pls),
                    names=names,
                ),
                parse_mode="HTML",
                reply_markup=playlists_keyboard(pls, lang),
            )
        except BackendError:
            await message.answer(
                tr("base.playlists.error", lang)
            )

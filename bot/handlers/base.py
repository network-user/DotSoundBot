import structlog
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.api.client import BackendClient, BackendError
from bot.keyboards.inline import (
    about_kb,
    back_to_about_kb,
    back_to_menu_kb,
    help_keyboard,
    main_menu_kb,
    playlists_keyboard,
    profile_kb,
)
from bot.utils.formatting import html_escape, safe_html

router = Router()
logger: structlog.stdlib.BoundLogger = (
    structlog.get_logger(__name__)
)

_ABOUT_TEXTS = {
    "features": (
        "🎵 <b>Возможности .sound</b>\n\n"
        ".sound — музыкальная платформа нового "
        "поколения прямо в Telegram. "
        "Без рекламы, без подписок.\n\n"
        "— Загружай свои треки в любом формате\n"
        "— Слушай музыку прямо в Mini App\n"
        "— Адаптивное качество: HLS стриминг\n"
        "  подстраивается под скорость (128k/64k)\n"
        "— Автоматическая генерация обложек\n"
        "— Лайки, дизлайки, плейлисты\n"
        "— Поиск по всей библиотеке\n"
        "— Инлайн-режим: ищи и делись "
        "треками в любом чате\n"
        "— Текст песен с синхронизацией\n"
        "— Профиль автора со статистикой\n"
        "— Подписки на авторов и лента новинок"
    ),
    "tech": (
        "⚙️ <b>Технологии</b>\n\n"
        "Backend: Python, FastAPI, SQLAlchemy, "
        "PostgreSQL\n"
        "Хранилище: MinIO (S3-совместимое)\n"
        "Очереди: Taskiq + Redis\n"
        "Бот: aiogram 3, aiohttp\n"
        "Frontend: React, TypeScript, Vite\n"
        "Стриминг: HLS adaptive bitrate (hls.js)\n"
        "Транскодирование: FFmpeg "
        "(MP3 192k + AAC 128k/64k)\n\n"
        "Весь стек асинхронный. Аудио "
        "обрабатывается в фоне через "
        "распределённую очередь задач."
    ),
    "upload": (
        "📤 <b>Как загрузить музыку</b>\n\n"
        "<b>Способ 1 — Через бота:</b>\n"
        "Просто отправь аудиофайл в этот чат. "
        "Бот загрузит его автоматически.\n\n"
        "<b>Способ 2 — Через Mini App:</b>\n"
        "Открой плеер → «Загрузить» → выбери файл. "
        "Можно добавить обложку, жанр и текст.\n\n"
        "<b>Форматы:</b> "
        "MP3, OGG, WAV, FLAC, AAC, M4A\n"
        "<b>Макс. размер:</b> 100 МБ\n"
        "<b>Квота:</b> 3 ГБ на пользователя"
    ),
    "import": (
        "📥 <b>Импорт из Telegram</b>\n\n"
        "Импортируй музыку из своего профиля "
        "Telegram прямо в .sound.\n\n"
        "<b>Как это работает:</b>\n"
        "1. Открой плеер → Профиль → Импорт\n"
        "2. Выбери «Telegram»\n"
        "3. Бот найдёт треки из твоего профиля\n"
        "4. Выбери нужные → «Импортировать»\n\n"
        "Импорт идёт в фоне — можно закрыть окно. "
        "Треки появятся с меткой <b>TG</b>.\n\n"
        "<i>Скоро: VK, Яндекс, Spotify, "
        "SoundCloud</i>"
    ),
    "opensource": (
        "💻 <b>Открытый код</b>\n\n"
        ".sound — open source проект.\n\n"
        "<b>Два репозитория:</b>\n"
        "— DotSoundBackend — API, БД, стриминг\n"
        "— DotSoundBot — Telegram бот\n\n"
        "Стек полностью асинхронный, "
        "код самодокументирующийся.\n\n"
        "Хочешь внести вклад? Форкни и отправь PR."
    ),
    "roadmap": (
        "🚀 <b>Планы на будущее</b>\n\n"
        "— Импорт из VK, Яндекс, Spotify\n"
        "— Рекомендации на основе лайков\n"
        "— Совместные плейлисты\n"
        "— Эквалайзер и настройки звука\n"
        "— Оффлайн-режим (кэш треков)\n"
        "— Подкасты и аудиокниги\n"
        "— Монетизация для авторов\n"
        "— Telegram Premium интеграция\n\n"
        "<i>Следи за обновлениями!</i>"
    ),
}


def _main_menu_text(name: str | None) -> str:
    safe_name = html_escape(name or "друг")
    return (
        f"Привет, <b>{safe_name}</b>! 👋\n\n"
        "Добро пожаловать в <b>.sound</b> — "
        "музыка без рекламы.\n"
        "Слушай. Делись. Открывай."
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

    await message.answer(
        _main_menu_text(user.first_name),
        reply_markup=main_menu_kb(),
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
    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            _main_menu_text(name),
            reply_markup=main_menu_kb(),
        )


@router.callback_query(F.data == "menu:about")
async def on_about(
    callback: CallbackQuery,
) -> None:
    await callback.answer()
    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            "ℹ️ <b>О проекте .sound</b>\n\n"
            "Музыкальная платформа без рекламы "
            "в Telegram.\n"
            "Выбери раздел:",
            reply_markup=about_kb(),
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
    text = _ABOUT_TEXTS.get(section)
    if not text:
        await callback.answer("Раздел не найден")
        return
    await callback.answer()
    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            text,
            reply_markup=back_to_about_kb(),
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
                f"👤 <b>{safe_name}</b>\n"
                f"{username_str}\n"
                f"🎵 Треков: "
                f"<b>{stats.get('total_tracks', 0)}"
                f"</b>\n"
                f"▶️ Прослушиваний: "
                f"<b>{stats.get('total_plays', 0)}"
                f"</b>\n"
                f"❤️ Лайков: "
                f"<b>{stats.get('total_likes', 0)}"
                f"</b>\n"
                f"👥 Подписчиков: "
                f"<b>"
                f"{stats.get('followers_count', 0)}"
                f"</b>"
            )
        except BackendError:
            text = (
                "Не удалось загрузить профиль. "
                "Попробуй позже."
            )

    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            text,
            reply_markup=profile_kb(),
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
                text = (
                    "🔐 <b>История входов</b>\n\n"
                    "Нет записей о входах."
                )
            else:
                lines = [
                    "🔐 <b>История входов</b>\n"
                ]
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
                        f"{i}. {dt} — "
                        f"{device} — {ip}"
                    )
                lines.append(
                    "\n<i>Последние 10 входов</i>"
                )
                text = "\n".join(lines)
        except BackendError:
            text = (
                "Не удалось загрузить историю. "
                "Попробуй позже."
            )

    if callback.message and isinstance(
        callback.message, Message
    ):
        await callback.message.edit_text(
            text,
            reply_markup=back_to_menu_kb(),
        )


@router.message(F.text == "/help")
async def cmd_help(message: Message) -> None:
    structlog.contextvars.bind_contextvars(
        handler="cmd_help"
    )
    await message.answer(
        "Что умеет .sound:\n\n"
        "🎵 <b>Плеер</b> — слушай прямо "
        "в Telegram\n"
        "🔍 <b>Поиск</b> — введи название\n"
        "▤ <b>Плейлисты</b> — создавай подборки\n"
        "❤️ <b>Лайки</b> — сохраняй треки\n"
        "👤 <b>Профиль</b> — статистика\n"
        "📊 /mystats — статистика в чате",
        parse_mode="HTML",
        reply_markup=help_keyboard(),
    )


@router.message(F.text == "/profile")
async def cmd_profile(message: Message) -> None:
    if not message.from_user:
        return
    user = message.from_user

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
                f"👤 <b>{safe_name}</b>\n\n"
                f"🎵 Треков: "
                f"<b>{stats.get('total_tracks', 0)}"
                f"</b>\n"
                f"▶️ Прослушиваний: "
                f"<b>{stats.get('total_plays', 0)}"
                f"</b>\n"
                f"❤️ Лайков: "
                f"<b>{stats.get('total_likes', 0)}"
                f"</b>",
                parse_mode="HTML",
                reply_markup=profile_kb(),
            )
        except BackendError:
            await message.answer(
                "Не удалось загрузить профиль."
            )


@router.message(F.text == "/playlists")
async def cmd_playlists(
    message: Message,
) -> None:
    if not message.from_user:
        return
    user = message.from_user

    async with BackendClient() as client:
        try:
            pls = (
                await client.get_user_playlists(
                    user.id
                )
            )
            if not pls:
                await message.answer(
                    "У тебя пока нет плейлистов.\n"
                    "Открой плеер и создай первый!",
                    reply_markup=main_menu_kb(),
                )
                return
            names = "\n".join(
                f"▤ <b>{safe_html(pl.get('name'), 60)}</b>"
                for pl in pls[:10]
            )
            await message.answer(
                f"Твои плейлисты "
                f"({len(pls)}):\n\n{names}",
                parse_mode="HTML",
                reply_markup=playlists_keyboard(pls),
            )
        except BackendError:
            await message.answer(
                "Не удалось загрузить плейлисты."
            )

import structlog
from aiogram import F, Router
from aiogram.types import Message

from bot.api.client import BackendClient, BackendError
from bot.i18n.core import resolve_lang, tr
from bot.utils.formatting import safe_html

router = Router()
logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


@router.message(F.text.regexp(r"^/artist\s+\d+$"))
async def cmd_artist_detail(message: Message) -> None:
    if not message.from_user or not message.text:
        return
    lang = resolve_lang(message.from_user.language_code)
    parts = message.text.strip().split()
    if len(parts) != 2:
        return
    try:
        artist_id = int(parts[1])
    except ValueError:
        return
    async with BackendClient() as client:
        try:
            token = await client._get_token_for_user(
                message.from_user.id
            )
            artist = await client.get_artist_detail(
                artist_id, token=token
            )
            rels = await client.get_artist_catalog_releases(
                artist_id, token=token
            )
        except BackendError as exc:
            logger.warning(
                "artist_detail_failed",
                artist_id=artist_id,
                status=exc.status_code,
            )
            await message.answer(
                tr("artists.detail_error", lang)
            )
            return
    name = safe_html(str(artist.get("name", "")), 120)
    disc = artist.get("discography") or []
    disc_lines: list[str] = []
    for row in disc[:5]:
        if not isinstance(row, dict):
            continue
        title = safe_html(str(row.get("title", "")), 120)
        year = row.get("year")
        suffix = f" ({year})" if isinstance(year, int) else ""
        if title:
            disc_lines.append(f"• {title}{suffix}")
    rel_items = rels.get("items") if isinstance(rels, dict) else []
    rel_lines: list[str] = []
    if isinstance(rel_items, list):
        for row in rel_items[:5]:
            if not isinstance(row, dict):
                continue
            r_title = safe_html(str(row.get("title", "")), 120)
            if not r_title:
                continue
            r_count = row.get("track_count")
            if isinstance(r_count, int):
                rel_lines.append(f"• {r_title} ({r_count})")
            else:
                rel_lines.append(f"• {r_title}")
    text = (
        f"▤ <b>{name}</b>\n\n"
        f"<b>Discography</b>\n"
        f"{chr(10).join(disc_lines) if disc_lines else '—'}\n\n"
        f"<b>Catalog releases</b>\n"
        f"{chr(10).join(rel_lines) if rel_lines else '—'}"
    )
    await message.answer(text, parse_mode="HTML")

from html import escape


def truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def html_escape(value: object | None) -> str:
    """Escape arbitrary user-provided value for HTML parse_mode."""
    if value is None:
        return ""
    return escape(str(value), quote=False)


def safe_html(text: str | None, max_len: int) -> str:
    """Escape and truncate user content safely for HTML output."""
    if not text:
        return ""
    return html_escape(truncate(str(text), max_len))


_SOURCE_LABELS = {
    "my": "Мои треки",
    "liked": "Лайки",
    "feed": "Лента",
}


def format_player_message(
    source: str,
    tracks: list[dict],
    page: int,
    total: int | None = None,
) -> str:
    label = _SOURCE_LABELS.get(source, source)
    start = (page - 1) * len(tracks) + 1
    end = start + len(tracks) - 1

    header = (
        f"🎧 <b>Плеер — {html_escape(label)}</b>\n"
    )
    if total is not None and total > 0:
        header += f"Треки {start}–{end} из {total}\n"
    header += "\n"

    lines: list[str] = []
    for i, t in enumerate(tracks, start=1):
        title = safe_html(
            t.get("title", "Без названия"), 40
        )
        artist_raw = t.get("artist") or t.get(
            "performer", ""
        )
        artist = safe_html(artist_raw or None, 40)
        if artist:
            lines.append(
                f"{i}. {title} — {artist}"
            )
        else:
            lines.append(f"{i}. {title}")

    if not lines:
        return header + "Нет треков."

    return header + "\n".join(lines)


from html import escape

from bot.i18n.core import tr


def truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def html_escape(value: object | None) -> str:
    if value is None:
        return ""
    return escape(str(value), quote=False)


def format_main_menu_welcome(
    name: str | None, lang: str
) -> str:
    safe = html_escape(
        name or tr("base.friend", lang),
    )
    return tr("base.welcome", lang).format(
        name=safe,
    )


def safe_html(text: str | None, max_len: int | None = None) -> str:
    if not text:
        return ""
    s = str(text)
    if max_len is not None:
        s = truncate(s, max_len)
    return html_escape(s)


def format_player_message(
    source: str,
    tracks: list[dict],
    page: int,
    total: int | None = None,
    lang: str = "en",
    page_size: int | None = None,
) -> str:
    label_map = {
        "my": tr("fmt.label.my", lang),
        "liked": tr("fmt.label.liked", lang),
        "feed": tr("fmt.label.feed", lang),
        "follows": tr("fmt.label.follows", lang),
        "playlists": tr("fmt.label.playlists", lang),
        "recommendations": tr(
            "fmt.label.recommendations", lang
        ),
    }
    label = label_map.get(source, source)
    effective_size = page_size if page_size is not None else len(tracks)
    start = (page - 1) * effective_size + 1
    end = start + len(tracks) - 1
    no_title = tr("fmt.untitled", lang)

    header = tr("fmt.header", lang).format(label=html_escape(label))
    if total is not None and total > 0:
        header += tr("fmt.tracks_range", lang).format(
            start=start,
            end=end,
            total=total,
        )
    header += "\n"

    lines: list[str] = []
    for i, track in enumerate(tracks, start=1):
        title = safe_html(
            track.get("title", no_title), 40
        )
        artist_raw = track.get("artist") or track.get(
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
        return header + tr("fmt.empty", lang)

    return header + "\n".join(lines)

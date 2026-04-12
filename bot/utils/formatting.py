def truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


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

    header = f"🎧 <b>Плеер — {label}</b>\n"
    if total is not None and total > 0:
        header += f"Треки {start}–{end} из {total}\n"
    header += "\n"

    lines: list[str] = []
    for i, t in enumerate(tracks, start=1):
        title = truncate(
            t.get("title", "Без названия"), 40
        )
        artist = t.get("artist") or t.get(
            "performer", ""
        )
        if artist:
            lines.append(
                f"{i}. {title} — {artist}"
            )
        else:
            lines.append(f"{i}. {title}")

    if not lines:
        return header + "Нет треков."

    return header + "\n".join(lines)

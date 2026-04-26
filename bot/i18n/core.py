from __future__ import annotations

import bot.i18n.catalog as _catalog


def resolve_lang(code: str | None) -> str:
    if not code:
        return "en"
    c = str(code).lower().split("-", maxsplit=1)[0]
    if c in ("ru", "be", "uk", "kk"):
        return "ru"
    return "en"


def tr(key: str, lang: str) -> str:
    row = _catalog.STRINGS.get(key)
    if not row:
        return key
    v = row.get(lang)
    if v is not None:
        return v
    v = row.get("en")
    if v is not None:
        return v
    return key

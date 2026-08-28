"""Minus-phrase filter for named-search list scrape (search-system-v2)."""
from __future__ import annotations


def title_hits_exclude(title: str, exclude: list[str] | None) -> bool:
    """True if title contains any exclude phrase (case-insensitive substring)."""
    if not exclude:
        return False
    hay = (title or "").casefold()
    if not hay:
        return False
    for raw in exclude:
        phrase = str(raw or "").strip()
        if phrase and phrase.casefold() in hay:
            return True
    return False


def filter_rows_by_exclude(rows: list[dict], exclude: list[str] | None) -> list[dict]:
    """Drop list rows whose title matches any minus phrase."""
    if not exclude:
        return rows
    cleaned = [str(x).strip() for x in exclude if str(x or "").strip()]
    if not cleaned:
        return rows
    return [row for row in rows if not title_hits_exclude(str(row.get("title") or ""), cleaned)]

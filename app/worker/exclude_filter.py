"""Minus-phrase filter for named-search list scrape (search-system-v2)."""
from __future__ import annotations

from app.scoring.rules import is_ndt_control_service
from app.worker.search_seeds import _SUPPLY_EXCLUDE

_SUPPLY_EXCLUDE_FOLDED = frozenset(p.casefold() for p in _SUPPLY_EXCLUDE)


def title_hits_exclude(title: str, exclude: list[str] | None) -> bool:
    """True if title contains any exclude phrase (case-insensitive substring)."""
    if not exclude:
        return False
    hay = (title or "").casefold()
    if not hay:
        return False
    skip_supply = is_ndt_control_service(title)
    for raw in exclude:
        phrase = str(raw or "").strip()
        folded = phrase.casefold()
        if skip_supply and folded in _SUPPLY_EXCLUDE_FOLDED:
            continue
        if phrase and folded in hay:
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

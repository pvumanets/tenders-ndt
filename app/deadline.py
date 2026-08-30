"""MSK calendar-day helpers for inbox expiry and scrape filters."""
from __future__ import annotations

import re
from datetime import date

from app.worker.list_scrape import today_msk

_ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
_DMY_DATE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})")
_DMY_SHORT = re.compile(r"^(\d{2})\.(\d{2})\.(\d{2})\b")


def deadline_date(text: str | None) -> date | None:
    if not text:
        return None
    raw = text.strip()
    iso = _ISO_DATE.match(raw)
    if iso:
        try:
            return date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
        except ValueError:
            return None
    dmy = _DMY_DATE.match(raw)
    if dmy:
        try:
            return date(int(dmy.group(3)), int(dmy.group(2)), int(dmy.group(1)))
        except ValueError:
            return None
    short = _DMY_SHORT.match(raw)
    if short:
        try:
            yy = int(short.group(3))
            year = 2000 + yy if yy < 100 else yy
            return date(year, int(short.group(2)), int(short.group(1)))
        except ValueError:
            return None
    return None


def today_msk_date(today: date | None = None) -> date:
    if today is not None:
        return today
    return today_msk().date()


def is_deadline_expired(deadline_msk: str | None, today: date | None = None) -> bool:
    """True when calendar deadline is strictly before today (MSK). Undated → False."""
    due = deadline_date(deadline_msk)
    if due is None:
        return False
    return due < today_msk_date(today)


def drop_past_deadline_rows(
    rows: list[dict],
    *,
    today: date | None = None,
) -> tuple[list[dict], int]:
    """Remove rows with a known deadline strictly before today MSK.

    Undated rows are kept (list scrape may lack deadline; board hides undated separately).
    Used after card enrich so platforms that only learn the date on the card
    (e.g. Roseltorg www list) do not land past-deadline lots in the inbox.
    """
    kept: list[dict] = []
    dropped = 0
    for row in rows:
        raw = row.get("deadline_msk")
        text = str(raw).strip() if raw is not None else None
        if text == "":
            text = None
        if is_deadline_expired(text, today=today):
            dropped += 1
            continue
        kept.append(row)
    return kept, dropped


def deadline_iso(text: str | None) -> str | None:
    parsed = deadline_date(text)
    if parsed is not None:
        return parsed.isoformat()
    stripped = (text or "").strip()
    return stripped or None

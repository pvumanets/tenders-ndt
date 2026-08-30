"""Daily auto-run slot (MSK) — GET/PUT /api/schedule + ticker helpers."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.db.models import ScheduleSettings
from app.db.session import session_factory

MSK = ZoneInfo("Europe/Moscow")
SCHEDULE_ID = 1
DEFAULT_TIME_MSK = "07:00"
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
SKIP_ALREADY_RUNNING = "already_running"
SKIP_EMPTY_QUEUE = "empty_queue"


class ScheduleError(ValueError):
    """Invalid schedule payload — map to HTTP 400."""


def parse_time_msk(value: str | None) -> str:
    if value is None or not str(value).strip():
        raise ScheduleError("invalid_time_msk")
    text = str(value).strip()
    if _TIME_RE.match(text) is None:
        raise ScheduleError("invalid_time_msk")
    return text


def now_msk(now: datetime | None = None) -> datetime:
    if now is None:
        return datetime.now(MSK)
    if now.tzinfo is None:
        return now.replace(tzinfo=MSK)
    return now.astimezone(MSK)


def msk_date_of(stamp: datetime | None, *, today: date | None = None) -> date | None:
    if stamp is None:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(MSK).date()


def already_attempted_today(
    last_attempt_at: datetime | None,
    *,
    today: date | None = None,
    now: datetime | None = None,
) -> bool:
    day = today if today is not None else now_msk(now).date()
    attempt_day = msk_date_of(last_attempt_at)
    return attempt_day == day


def is_slot_due(
    time_msk: str,
    *,
    now: datetime | None = None,
) -> bool:
    current = now_msk(now)
    parsed = parse_time_msk(time_msk)
    hour, minute = (int(part) for part in parsed.split(":"))
    return (current.hour, current.minute, current.second) >= (hour, minute, 0)


def next_fire_at(
    *,
    enabled: bool,
    time_msk: str,
    last_attempt_at: datetime | None,
    now: datetime | None = None,
) -> datetime | None:
    if not enabled:
        return None
    current = now_msk(now)
    parsed = parse_time_msk(time_msk)
    hour, minute = (int(part) for part in parsed.split(":"))
    today_slot = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if already_attempted_today(last_attempt_at, today=current.date()) or current >= today_slot:
        return today_slot + timedelta(days=1)
    return today_slot


def _iso(stamp: datetime | None) -> str | None:
    if stamp is None:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc).isoformat()


def _row_payload(row: ScheduleSettings, *, now: datetime | None = None) -> dict[str, Any]:
    nxt = next_fire_at(
        enabled=bool(row.enabled),
        time_msk=row.time_msk,
        last_attempt_at=row.last_attempt_at,
        now=now,
    )
    return {
        "enabled": bool(row.enabled),
        "time_msk": row.time_msk,
        "last_fired_at": _iso(row.last_fired_at),
        "last_skip_reason": row.last_skip_reason,
        "last_attempt_at": _iso(row.last_attempt_at),
        "next_fire_at": _iso(nxt),
    }


def _ensure_row(session) -> ScheduleSettings:
    row = session.get(ScheduleSettings, SCHEDULE_ID)
    if row is not None:
        return row
    row = ScheduleSettings(
        id=SCHEDULE_ID,
        enabled=True,
        time_msk=DEFAULT_TIME_MSK,
    )
    session.add(row)
    session.flush()
    return row


def get_schedule(*, now: datetime | None = None) -> dict[str, Any]:
    factory = session_factory()
    with factory() as session:
        row = _ensure_row(session)
        session.commit()
        return _row_payload(row, now=now)


def put_schedule(body: dict[str, Any] | None, *, now: datetime | None = None) -> dict[str, Any]:
    payload = body if isinstance(body, dict) else {}
    enabled = payload.get("enabled") if "enabled" in payload else None
    time_raw = payload.get("time_msk") if "time_msk" in payload else None
    time_msk = parse_time_msk(time_raw) if time_raw is not None else None
    factory = session_factory()
    with factory() as session:
        row = _ensure_row(session)
        if enabled is not None:
            row.enabled = enabled
        if time_msk is not None:
            row.time_msk = time_msk
        row.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(row)
        return _row_payload(row, now=now)


def record_slot_skip(reason: str, *, now: datetime | None = None) -> None:
    stamp = datetime.now(timezone.utc) if now is None else now.astimezone(timezone.utc)
    factory = session_factory()
    with factory() as session:
        row = _ensure_row(session)
        row.last_skip_reason = reason
        row.last_attempt_at = stamp
        row.updated_at = stamp
        session.commit()


def record_slot_fire(*, now: datetime | None = None) -> None:
    stamp = datetime.now(timezone.utc) if now is None else now.astimezone(timezone.utc)
    factory = session_factory()
    with factory() as session:
        row = _ensure_row(session)
        row.last_fired_at = stamp
        row.last_attempt_at = stamp
        row.last_skip_reason = None
        row.updated_at = stamp
        session.commit()


def tick_once(*, now: datetime | None = None, start_auto=None) -> str:
    """Return idle|skipped|fired. start_auto() starts pipeline=auto (internal)."""
    from app.api.state import STATE

    current = now_msk(now)
    try:
        factory = session_factory()
    except RuntimeError:
        return "idle"
    with factory() as session:
        row = _ensure_row(session)
        session.commit()
        enabled = bool(row.enabled)
        time_msk = row.time_msk
        last_attempt_at = row.last_attempt_at
    if not enabled:
        return "idle"
    if already_attempted_today(last_attempt_at, today=current.date()):
        return "idle"
    if not is_slot_due(time_msk, now=current):
        return "idle"
    if STATE.snapshot()["running"]:
        record_slot_skip(SKIP_ALREADY_RUNNING, now=current)
        return "skipped"
    starter = start_auto
    if starter is None:
        from app.api.runner import start_run

        def starter() -> bool:
            return start_run(pipeline="auto", from_ticker=True)

    try:
        started = starter()
    except RuntimeError as exc:
        detail = str(exc)
        if detail in {SKIP_ALREADY_RUNNING, SKIP_EMPTY_QUEUE}:
            record_slot_skip(detail, now=current)
            return "skipped"
        raise
    if started is False:
        return "skipped"
    return "fired"

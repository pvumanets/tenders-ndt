"""Unit: schedule parse, once-per-day, skip reasons. No database required."""
from __future__ import annotations

from datetime import datetime

import pytest

from app.api.schedule import (
    SKIP_ALREADY_RUNNING,
    already_attempted_today,
    is_slot_due,
    next_fire_at,
    now_msk,
    parse_time_msk,
    ScheduleError,
    tick_once,
)
from app.api.state import STATE


@pytest.mark.unit
def test_parse_time_msk() -> None:
    assert parse_time_msk("07:00") == "07:00"
    assert parse_time_msk("23:59") == "23:59"
    assert parse_time_msk("00:00") == "00:00"
    with pytest.raises(ScheduleError, match="invalid_time_msk"):
        parse_time_msk("7:00")
    with pytest.raises(ScheduleError, match="invalid_time_msk"):
        parse_time_msk("24:00")
    with pytest.raises(ScheduleError, match="invalid_time_msk"):
        parse_time_msk("ab:cd")
    with pytest.raises(ScheduleError, match="invalid_time_msk"):
        parse_time_msk("")


@pytest.mark.unit
def test_already_attempted_today() -> None:
    now = datetime(2026, 8, 30, 10, 0, tzinfo=now_msk().tzinfo)
    attempt = datetime(2026, 8, 30, 7, 0, tzinfo=now_msk().tzinfo)
    yesterday = datetime(2026, 8, 29, 7, 0, tzinfo=now_msk().tzinfo)
    assert already_attempted_today(attempt, now=now) is True
    assert already_attempted_today(yesterday, now=now) is False
    assert already_attempted_today(None, now=now) is False


@pytest.mark.unit
def test_is_slot_due_and_next_fire() -> None:
    now = datetime(2026, 8, 30, 6, 59, tzinfo=now_msk().tzinfo)
    assert is_slot_due("07:00", now=now) is False
    due = datetime(2026, 8, 30, 7, 0, tzinfo=now_msk().tzinfo)
    assert is_slot_due("07:00", now=due) is True
    nxt = next_fire_at(enabled=True, time_msk="07:00", last_attempt_at=None, now=now)
    assert nxt is not None
    assert nxt.hour == 7
    assert nxt.date() == now.date()
    after = next_fire_at(enabled=True, time_msk="07:00", last_attempt_at=due, now=due)
    assert after is not None
    assert after.date() > due.date()
    assert next_fire_at(enabled=False, time_msk="07:00", last_attempt_at=None, now=now) is None


@pytest.mark.unit
def test_tick_once_idle_without_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.api.schedule.session_factory",
        lambda: (_ for _ in ()).throw(RuntimeError("database_unconfigured")),
    )
    assert tick_once() == "idle"


@pytest.mark.unit
def test_tick_once_skips_when_running(monkeypatch: pytest.MonkeyPatch) -> None:
    from datetime import timezone as tz

    from app.db.models import ScheduleSettings

    row = ScheduleSettings(
        id=1,
        enabled=True,
        time_msk="00:00",
        updated_at=datetime.now(tz.utc),
    )

    class _Sess:
        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

        def get(self, *_a, **_k):
            return row

        def add(self, *_a):
            return None

        def flush(self):
            return None

        def commit(self):
            return None

    class _Factory:
        def __call__(self):
            return _Sess()

    monkeypatch.setattr("app.api.schedule.session_factory", lambda: _Factory())
    STATE.running = True
    try:
        assert tick_once() == "skipped"
        assert row.last_skip_reason == SKIP_ALREADY_RUNNING
    finally:
        STATE.running = False

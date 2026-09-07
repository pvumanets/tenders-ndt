"""Unit: TTL cache for live session probes (082). No ETP."""
from __future__ import annotations

import pytest

from app.api import session_probe
from app.api.state import STATE


@pytest.fixture(autouse=True)
def _reset_probe_cache() -> None:
    session_probe.reset_for_tests()
    yield
    session_probe.reset_for_tests()


@pytest.mark.unit
def test_two_cached_status_calls_one_live_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []

    def fake_refresh(*, probe_roseltorg_live: bool = True) -> str:
        calls.append(probe_roseltorg_live)
        STATE.set_session("ok")
        return "ok"

    monkeypatch.setattr("app.api.runner.refresh_session", fake_refresh)
    first = session_probe.refresh_session_cached(probe_roseltorg_live=False)
    second = session_probe.refresh_session_cached(probe_roseltorg_live=False)
    assert first == "ok"
    assert second == "ok"
    assert calls == [False]
    assert session_probe.live_call_count() == 1


@pytest.mark.unit
def test_force_refresh_bypasses_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def fake_refresh(*, probe_roseltorg_live: bool = True) -> str:
        del probe_roseltorg_live
        calls.append(1)
        STATE.set_session("ok")
        return "ok"

    monkeypatch.setattr("app.api.runner.refresh_session", fake_refresh)
    session_probe.refresh_session_cached()
    session_probe.refresh_session_cached(force=True)
    assert calls == [1, 1]
    assert session_probe.live_call_count() == 2

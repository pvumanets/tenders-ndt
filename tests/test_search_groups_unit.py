"""Unit: 048 queue expand groups × platforms."""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.api import search_groups as search_groups_api


@pytest.mark.unit
def test_get_queued_steps_cartesian(monkeypatch: pytest.MonkeyPatch) -> None:
    g1 = uuid4()
    g2 = uuid4()

    class FakeGroup:
        def __init__(self, gid, name, sort_order):
            self.id = gid
            self.name = name
            self.queries = ["q"]
            self.exclude = []
            self.limit_n = 0
            self.in_queue = True
            self.sort_order = sort_order

    class FakeSetting:
        def __init__(self, platform_id, enabled):
            self.platform_id = platform_id
            self.enabled = enabled

    class FakeScalars:
        def __init__(self, rows):
            self._rows = rows

        def all(self):
            return self._rows

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def scalars(self, stmt):
            # First call loads groups; second loads platform_settings (order in get_queued_steps).
            if not hasattr(self, "_n"):
                self._n = 0
            self._n += 1
            if self._n == 1:
                return FakeScalars(
                    [
                        FakeGroup(g1, "услуги НК", 1),
                        FakeGroup(g2, "методы", 2),
                    ]
                )
            return FakeScalars(
                [
                    FakeSetting("rostender", True),
                    FakeSetting("tender-pro", True),
                    FakeSetting("roseltorg", False),
                ]
            )

    class FakeFactory:
        def __call__(self):
            return FakeSession()

    monkeypatch.setattr(search_groups_api, "session_factory", lambda: FakeFactory())

    steps = search_groups_api.get_queued_steps()
    assert len(steps) == 4
    assert [s["platform_id"] for s in steps] == [
        "rostender",
        "tender-pro",
        "rostender",
        "tender-pro",
    ]
    assert steps[0]["group_name"] == "услуги НК"
    assert steps[0]["group_id"] == str(g1)
    assert steps[0]["id"] != steps[1]["id"]
    assert steps[0]["group_id"] == steps[1]["group_id"]


@pytest.mark.unit
def test_cookie_sync_enables_only_never_disables(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api import search_queue_sync as sync

    calls: list[tuple[str, bool]] = []

    def capture(platform_id: str, want: bool) -> None:
        calls.append((platform_id, want))

    monkeypatch.setattr(sync, "_set_platform_enabled", capture)
    monkeypatch.setattr(sync, "tender_pro_cookies_present", lambda: False)
    monkeypatch.setattr(sync, "roseltorg_cookies_present", lambda: False)
    sync.sync_tender_pro_queue_from_cookies()
    sync.sync_roseltorg_queue_from_credentials()
    assert calls == []

    monkeypatch.setattr(sync, "tender_pro_cookies_present", lambda: True)
    monkeypatch.setattr(sync, "roseltorg_cookies_present", lambda: True)
    sync.sync_tender_pro_queue_from_cookies()
    sync.sync_roseltorg_queue_from_credentials()
    assert calls == [
        (sync.PLATFORM_TENDER_PRO, True),
        (sync.PLATFORM_ROSELTORG, True),
    ]

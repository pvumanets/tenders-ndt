"""Unit: auto-AI selector include/exclude + empty prefer no-op."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.api.inbox import lot_eligible_for_auto_ai, select_auto_ai_ids
from app.api.notify import notify_auto_l1


def _row(**overrides: object) -> dict:
    values: dict = {
        "tender_id": "rostender:qa_auto_1",
        "tier": "L1",
        "deadline_msk": "01.01.2027",
        "board_hidden": False,
        "ai_reviewed_at": None,
    }
    values.update(overrides)
    return values


@pytest.mark.unit
def test_lot_eligible_for_auto_ai() -> None:
    assert lot_eligible_for_auto_ai(
        tier="L1",
        deadline_msk="01.01.2027",
        board_hidden=False,
        ai_reviewed_at=None,
    )
    assert lot_eligible_for_auto_ai(
        tier="L3",
        deadline_msk="01.01.2027",
        board_hidden=False,
        ai_reviewed_at=None,
    )
    assert not lot_eligible_for_auto_ai(
        tier="noise",
        deadline_msk="01.01.2027",
        board_hidden=False,
        ai_reviewed_at=None,
    )
    assert not lot_eligible_for_auto_ai(
        tier="L1",
        deadline_msk="01.01.2027",
        board_hidden=True,
        ai_reviewed_at=None,
    )
    assert not lot_eligible_for_auto_ai(
        tier="L1",
        deadline_msk="01.01.2020",
        board_hidden=False,
        ai_reviewed_at=None,
    )
    assert not lot_eligible_for_auto_ai(
        tier="L1",
        deadline_msk="01.01.2027",
        board_hidden=False,
        ai_reviewed_at=datetime(2026, 8, 30, tzinfo=timezone.utc),
    )


@pytest.mark.unit
def test_select_auto_ai_empty_prefer_is_noop() -> None:
    rows = [_row(), _row(tender_id="rostender:qa_auto_2", tier="L2")]
    assert select_auto_ai_ids(rows, prefer_ids=set()) == []


@pytest.mark.unit
def test_select_auto_ai_prefer_intersection() -> None:
    keep = _row(tender_id="rostender:keep")
    hidden = _row(tender_id="rostender:hidden", board_hidden=True)
    reviewed = _row(
        tender_id="rostender:reviewed",
        ai_reviewed_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
    )
    other = _row(tender_id="rostender:other")
    noise = _row(tender_id="rostender:noise", tier="noise")
    ids = select_auto_ai_ids(
        [keep, hidden, reviewed, other, noise],
        prefer_ids={"rostender:keep", "rostender:hidden", "rostender:reviewed", "rostender:noise"},
    )
    assert ids == ["rostender:keep"]


@pytest.mark.unit
def test_notify_auto_l1_empty_noop() -> None:
    notify_auto_l1([])


@pytest.mark.unit
def test_notify_auto_l1_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []

    def fake(ids: list[str]) -> dict[str, int]:
        seen.append(ids)
        return {"sent": 0, "skipped": 1, "failed": 0}

    monkeypatch.setattr("app.api.notify.notify_auto_l1_lots", fake)
    notify_auto_l1(["rostender:qa_l1"])
    assert seen == [["rostender:qa_l1"]]

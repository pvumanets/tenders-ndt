"""Unit: past-deadline drop before ingest (Roseltorg card-enrich hole)."""
from __future__ import annotations

from datetime import date

import pytest

from app.deadline import drop_past_deadline_rows, is_deadline_expired


@pytest.mark.unit
def test_drop_past_deadline_keeps_live_and_undated() -> None:
    today = date(2026, 8, 29)
    rows = [
        {"tender_id": "a", "deadline_msk": "18.08.2026", "tier": "L1"},
        {"tender_id": "b", "deadline_msk": "29.08.2026", "tier": "L1"},
        {"tender_id": "c", "deadline_msk": "08.09.2026", "tier": "L2"},
        {"tender_id": "d", "deadline_msk": None, "tier": "L1"},
        {"tender_id": "e", "deadline_msk": "2026-08-03", "tier": "L3"},
    ]
    kept, dropped = drop_past_deadline_rows(rows, today=today)
    assert dropped == 2
    assert [r["tender_id"] for r in kept] == ["b", "c", "d"]


@pytest.mark.unit
def test_is_deadline_expired_boundary() -> None:
    today = date(2026, 8, 29)
    assert is_deadline_expired("28.08.2026", today=today) is True
    assert is_deadline_expired("29.08.2026", today=today) is False
    assert is_deadline_expired(None, today=today) is False

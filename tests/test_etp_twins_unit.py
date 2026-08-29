"""Unit: Росэлторг twin prefer over РосТендер."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.worker import etp_twins
from app.worker.platform_ids import compose_tender_id


@pytest.mark.unit
def test_hide_rostender_twins_for_roseltorg() -> None:
    session = MagicMock()
    re_tid = compose_tender_id("roseltorg", "ATOM28082600172")
    rt_tid = compose_tender_id("rostender", "94646176")

    def get_side_effect(model, key=None, *args, **kwargs):
        # session.get(Lot, tid) or session.get(LotState, tid)
        name = getattr(model, "__name__", str(model))
        if name == "Lot" and key == re_tid:
            return SimpleNamespace(tender_id=re_tid)
        if name == "LotState":
            return None
        return None

    session.get.side_effect = get_side_effect
    twin = SimpleNamespace(
        tender_id=rt_tid,
        url="https://rostender.info/x",
        title="капиллярный ATOM28082600172",
        raw={"etp_procedure_id": "ATOM28082600172"},
        source_platform_id="rostender",
    )
    session.scalars.return_value.all.return_value = [twin]

    n = etp_twins.hide_rostender_twins_for_roseltorg(
        session, native_ids=["ATOM28082600172"]
    )
    assert n == 1
    assert session.add.called


@pytest.mark.unit
def test_hide_if_roseltorg_exists() -> None:
    session = MagicMock()
    re_tid = compose_tender_id("roseltorg", "ATOM1")

    def get_side_effect(model, key=None, *args, **kwargs):
        name = getattr(model, "__name__", str(model))
        if name == "Lot" and key == re_tid:
            return SimpleNamespace(tender_id=re_tid)
        if name == "LotState":
            return None
        return None

    session.get.side_effect = get_side_effect
    ok = etp_twins.hide_if_roseltorg_exists(
        session,
        rostender_row={
            "tender_id": "rostender:1",
            "etp_procedure_id": "ATOM1",
            "url": "https://rostender.info/1",
            "title": "x",
        },
    )
    assert ok is True

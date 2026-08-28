"""Unit: minus-phrase list filter (036 / search-system-v2)."""
from __future__ import annotations

import pytest

from app.worker.exclude_filter import filter_rows_by_exclude, title_hits_exclude
from app.worker.search_seeds import search_seed_rows


@pytest.mark.unit
def test_title_hits_exclude_casefold() -> None:
    minus = ["ЗАГС", "кровля"]
    assert title_hits_exclude("Строительный контроль кровли ЗАГСа", minus) is True
    assert title_hits_exclude("КРОВЛЯ здания", ["кровля"]) is True
    assert title_hits_exclude("УЗК трубопровода", minus) is False
    assert title_hits_exclude("x", []) is False


@pytest.mark.unit
def test_filter_rows_drops_zags_roof_keeps_kindergarten_radiography() -> None:
    d_exclude = next(r for r in search_seed_rows() if r["name"] == "РосТендер — контроли")["exclude"]
    rows = [
        {
            "tender_id": "1",
            "title": "Оказание услуг строительного контроля кровли здания ЗАГС",
        },
        {
            "tender_id": "2",
            "title": "Радиографический контроль сварных соединений детсад №12",
        },
        {"tender_id": "3", "title": "Строительный контроль на промышленном объекте"},
    ]
    kept = filter_rows_by_exclude(rows, d_exclude)
    ids = {r["tender_id"] for r in kept}
    assert "1" not in ids
    assert "2" not in ids  # детсад in D exclude
    assert "3" in ids
    # Empty exclude keeps kindergarten radiography (package B)
    assert filter_rows_by_exclude([rows[1]], []) == [rows[1]]


@pytest.mark.unit
def test_seed_package_d_plus_minus() -> None:
    d = next(r for r in search_seed_rows() if r["name"] == "РосТендер — контроли")
    assert "строительный контроль" in d["queries"]
    for phrase in ("жилой", "кровля", "ЗАГС", "детсад", "дороги"):
        assert phrase in d["exclude"]
    for row in search_seed_rows():
        if row["name"] != "РосТендер — контроли":
            assert row["exclude"] == []

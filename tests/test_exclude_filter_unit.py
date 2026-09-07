"""Unit: minus-phrase list filter (036 / search-system-v2)."""
from __future__ import annotations

import pytest

from app.worker.exclude_filter import filter_rows_by_exclude, title_hits_exclude
from app.worker.search_seeds import _SUPPLY_EXCLUDE, search_seed_rows


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
    for phrase in ("жилой", "кровля", "ЗАГС", "детсад", "дороги", "поставка", "закупка", "прибор"):
        assert phrase in d["exclude"]
    for row in search_seed_rows():
        if row["name"] == "РосТендер — контроли":
            continue
        for phrase in _SUPPLY_EXCLUDE:
            assert phrase in row["exclude"], row["name"]


_E1 = "Закупка услуг по проведению неразрушающего контроля сварных соединений трубопроводов на НПЗ"
_E2 = "Поставка услуг по ультразвуковому контролю сварных соединений"
_E3 = "Оказание услуг по проведению неразрушающего контроля сварных соединений"
_E4 = "Закупка ультразвукового дефектоскопа"
_E5 = "Поставка приборов для визуального и измерительного контроля"
_E6 = "Закупку услуг по проведению неразрушающего контроля сварных соединений трубопроводов на НПЗ"
_E7 = "На поставку услуг по УЗК сварных соединений"


@pytest.mark.unit
@pytest.mark.parametrize("title", [_E1, _E2, _E3, _E6, _E7])
def test_supply_exclude_keeps_ndt_service_titles(title: str) -> None:
    assert title_hits_exclude(title, _SUPPLY_EXCLUDE) is False
    kept = filter_rows_by_exclude([{"tender_id": "1", "title": title}], _SUPPLY_EXCLUDE)
    assert kept == [{"tender_id": "1", "title": title}]


@pytest.mark.unit
@pytest.mark.parametrize("title", [_E4, _E5])
def test_supply_exclude_still_drops_devices(title: str) -> None:
    assert title_hits_exclude(title, _SUPPLY_EXCLUDE) is True


@pytest.mark.unit
def test_ndt_service_still_hits_non_supply_minus() -> None:
    title = "Закупка услуг по проведению неразрушающего контроля кровли ЗАГС"
    assert title_hits_exclude(title, _SUPPLY_EXCLUDE) is False
    assert title_hits_exclude(title, ["кровля", "ЗАГС", *_SUPPLY_EXCLUDE]) is True

"""Unit: 037 — supply exclude, no methods inject, score etalons."""
from __future__ import annotations

import pytest

from app.scoring.pipeline import rescore_rows, rescore_text, score_rows
from app.scoring.tiers import assign_tier
from app.worker.search_seeds import _SUPPLY_EXCLUDE, search_seed_rows


@pytest.mark.unit
def test_all_seeds_have_supply_exclude() -> None:
    for row in search_seed_rows():
        for phrase in _SUPPLY_EXCLUDE:
            assert phrase in row["exclude"], row["name"]


@pytest.mark.unit
def test_rescore_text_ignores_methods() -> None:
    row = {
        "title": "Поставка расходных материалов",
        "methods": "УЗК, НК",
        "description": "шум",
    }
    assert "УЗК" not in rescore_text(row)
    assert "НК" not in rescore_text(row)


@pytest.mark.unit
def test_rescore_does_not_promote_via_methods() -> None:
    base = [{"tender_id": "1", "title": "Поставка расходных материалов для клиники", "rank": 1}]
    scored, _, _ = score_rows(base)
    row = dict(scored[0])
    row["card_fetched"] = True
    row["methods"] = "УЗК, НК"
    rescored, _, _ = rescore_rows([row])
    assert rescored[0]["tier"] == scored[0]["tier"] == "L3"
    assert "uzk_service" not in (rescored[0].get("fit_reason") or "")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("title", "expected"),
    [
        (
            "Дефектоскоп для неразрушающего контроля стальных канатов",
            "L3",
        ),
        (
            "Поставка расходных материалов для клинической деятельности",
            "L3",
        ),
        (
            "Оказание услуг по поверке, калибровке средств измерений, метрологическому контролю",
            "L3",
        ),
        (
            "оказание услуг по проведению инструментального контроля медицинского оборудования Энергетиков, 38.",
            "pool",
        ),
        (
            "Проведение неразрушающего контроля сварных соединений",
            "L1",
        ),
    ],
)
def test_037_hot_junk_etalons(title: str, expected: str) -> None:
    tier, _score, _reason, _uzk = assign_tier(title)
    if expected == "L1":
        assert tier in {"L1", "L2"}
    else:
        assert tier == expected

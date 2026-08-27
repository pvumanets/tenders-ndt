"""P10 fit-tiers goldenset: services L1/L2; supply → L3 on board."""
from __future__ import annotations

import pytest

from app.scoring.tiers import assign_tier


@pytest.mark.unit
@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Проведение неразрушающего контроля сварных соединений", "L1"),
        ("Услуги по контролю толщины стенок трубопроводов методом НК", "L1"),
        ("Поставка оборудования для неразрушающего контроля", "L3"),
        ("Закупка дефектоскопа ультразвукового", "L3"),
        ("Калибровка толщиномера без оказания услуг НК", "L3"),
        ("Обучение персонала по неразрушающему контролю", "noise"),
    ],
)
def test_fit_tier_etalons(title: str, expected: str) -> None:
    tier, _score, _reason, _uzk = assign_tier(title)
    if expected == "L1":
        assert tier in {"L1", "L2"}
        if "Проведение" in title:
            assert tier == "L1"
    else:
        assert tier == expected

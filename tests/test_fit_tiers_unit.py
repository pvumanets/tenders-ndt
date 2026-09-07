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
        (
            "Закупка услуг по проведению неразрушающего контроля сварных соединений трубопроводов на НПЗ",
            "L1",
        ),
        ("Поставка услуг по ультразвуковому контролю сварных соединений", "L1"),
        ("Оказание услуг по проведению неразрушающего контроля сварных соединений", "L1"),
        (
            "Закупку услуг по проведению неразрушающего контроля сварных соединений трубопроводов на НПЗ",
            "L1",
        ),
        ("На поставку услуг по УЗК сварных соединений", "L1"),
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


@pytest.mark.unit
def test_construction_control_not_hard_l3() -> None:
    """036: стройконтроль без минуса не форсируется в L3 (откат 035)."""
    tier, _score, reason, _uzk = assign_tier("Услуги строительного контроля на объекте")
    assert "build_ctrl_l3" not in reason
    assert tier == "pool"


@pytest.mark.unit
@pytest.mark.parametrize(
    "title",
    [
        "Закупка услуг по проведению неразрушающего контроля сварных соединений трубопроводов на НПЗ",
        "Поставка услуг по ультразвуковому контролю сварных соединений",
        "Оказание услуг по проведению неразрушающего контроля сварных соединений",
        "Закупку услуг по проведению неразрушающего контроля сварных соединений трубопроводов на НПЗ",
        "На поставку услуг по УЗК сварных соединений",
    ],
)
def test_v1_procurement_of_ndt_service_is_l1(title: str) -> None:
    tier, score, _reason, _uzk = assign_tier(title)
    assert score >= 6
    assert tier == "L1"


@pytest.mark.unit
@pytest.mark.parametrize(
    "title",
    [
        "Закупка ультразвукового дефектоскопа",
        "Поставка приборов для визуального и измерительного контроля",
    ],
)
def test_device_supply_not_hot(title: str) -> None:
    """E4–E5: чистая поставка прибора не в Горячих."""
    tier, _score, _reason, _uzk = assign_tier(title)
    assert tier != "L1"
    assert tier in {"L3", "pool"}

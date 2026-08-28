"""Unit: 033 — no UK/RK false positives in scoring or seeds."""
from __future__ import annotations

import pytest

from app.scoring.rules import RE_RK, RE_UZK, score_title
from app.scoring.tiers import assign_tier
from app.worker.search_seeds import search_seed_rows

_VORONEZH_SMR = (
    "Конкурентный отбор в электронной форме на электронной торговой площадке на право "
    "заключения договора на выполнение строительно-монтажных работ по объекту: "
    "«Строительство, модернизация и реконструкция объектов на Левобережных очистных "
    "сооружениях г. Воронежа», проводимый централизованно ООО УК «РОСВОДОКАНАЛ» "
    "для нужд ООО «РВК-Воронеж»"
)


@pytest.mark.unit
def test_voronezh_smr_not_hot() -> None:
    tier, score, _reason, _uzk = assign_tier(_VORONEZH_SMR)
    assert tier != "L1"
    assert score < 6


@pytest.mark.unit
def test_uk_in_company_name_not_uzk_signal() -> None:
    assert RE_UZK.search("ООО УК «РОСВОДОКАНАЛ»") is None


@pytest.mark.unit
def test_uzk_still_scores() -> None:
    tier, _score, _reason, uzk = assign_tier("УЗК сварных швов на объекте")
    assert uzk is True
    assert tier in {"L1", "L2", "L3"}


@pytest.mark.unit
def test_radiograph_still_scores() -> None:
    _score, reasons, _uzk = score_title("радиографический контроль сварных соединений")
    assert any("ndt_service" in r for r in reasons)


@pytest.mark.unit
def test_plate_rk_not_radiography_signal() -> None:
    assert RE_RK.search("поставка для физической защиты РК НИЦ Курчатовский") is None


@pytest.mark.unit
def test_abbr_seeds_no_uk_rk() -> None:
    rows = search_seed_rows()
    rt = next(r for r in rows if r["name"] == "РосТендер — аббревиатуры")
    tp = next(r for r in rows if r["name"] == "Tender.Pro — аббревиатуры")
    for q in rt["queries"] + tp["queries"]:
        assert q.upper() not in {"УК", "РК"}
    assert "УЗК" in rt["queries"]
    assert "УЗК" in tp["queries"]

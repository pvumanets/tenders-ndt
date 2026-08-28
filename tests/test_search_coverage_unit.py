"""Unit: P11/030 — no must-cap 1000; seed packages A–E + Tender.Pro."""
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.api.searches import SearchIn
from app.worker import list_scrape
from app.worker.search_seeds import search_seed_rows


@pytest.mark.unit
def test_search_in_allows_zero_and_above_1000() -> None:
    zero = SearchIn.model_validate(
        {
            "name": "Unlimited",
            "platform_id": "rostender",
            "queries": ["НК"],
            "limit_n": 0,
        }
    )
    assert zero.limit_n == 0
    high = SearchIn.model_validate(
        {
            "name": "Wide",
            "platform_id": "rostender",
            "queries": ["НК"],
            "limit_n": 2500,
        }
    )
    assert high.limit_n == 2500
    with pytest.raises(ValidationError):
        SearchIn.model_validate(
            {
                "name": "Neg",
                "platform_id": "rostender",
                "queries": ["НК"],
                "limit_n": -1,
            }
        )


@pytest.mark.unit
def test_seed_rows_rostender_a_to_e_order() -> None:
    rows = search_seed_rows(tender_pro_in_queue=False)
    rt = [r for r in rows if r["platform_id"] == "rostender"]
    tp = [r for r in rows if r["platform_id"] == "tender-pro"]
    assert [r["name"] for r in rt] == [
        "РосТендер — услуги НК",
        "РосТендер — методы",
        "РосТендер — аббревиатуры",
        "РосТендер — контроли",
        "РосТендер — страховка",
    ]
    assert [r["sort_order"] for r in rt] == [1, 2, 3, 4, 5]
    assert all(r["in_queue"] is True for r in rt)
    assert all(r["limit_n"] == 0 for r in rows)
    assert [r["name"] for r in tp] == [
        "Tender.Pro — методы",
        "Tender.Pro — аббревиатуры",
        "Tender.Pro — контроли",
        "Tender.Pro — страховка",
    ]
    assert all(r["in_queue"] is False for r in tp)
    assert all(r["in_queue"] is True for r in search_seed_rows(tender_pro_in_queue=True) if r["platform_id"] == "tender-pro")
    re = [r for r in rows if r["platform_id"] == "roseltorg"]
    assert len(re) == 4
    assert all(r["in_queue"] is False for r in re)
    assert all(
        r["in_queue"] is True
        for r in search_seed_rows(roseltorg_in_queue=True)
        if r["platform_id"] == "roseltorg"
    )


@pytest.mark.unit
def test_scrape_queries_unlimited_not_capped_at_1000(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_scrape_list(*, query: str, limit: int, **_kwargs: object) -> list[dict]:
        # limit<=0 means unlimited soft stop (same as list_scrape.scrape_list)
        size = 600 if int(limit or 0) <= 0 else int(limit)
        return [{"tender_id": f"{query}-{i}", "title": f"{query}-{i}"} for i in range(size)]

    monkeypatch.setattr(list_scrape, "scrape_list", fake_scrape_list)
    rows = list_scrape.scrape_queries(
        cookies_path=Path("missing.txt"),
        queries=["a", "b"],
        limit=0,
    )
    assert len(rows) == 1200
    assert rows[0]["tender_id"] == "a-0"
    assert rows[600]["tender_id"] == "b-0"

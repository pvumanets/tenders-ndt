"""Unit: Росэлторг CORP mapping, open-filter, prefix (no live ELK)."""
from __future__ import annotations

from datetime import date

import pytest

from app.worker import roseltorg
from app.worker.platform_ids import PLATFORM_ROSELTORG, compose_tender_id, prefix_rows
from app.worker.search_seeds import search_seed_rows


_SAMPLE = {
    "id": 32616262401,
    "name": "Услуги ультразвукового контроля",
    "organizator": "ООО Тест",
    "acceptanceApplicationsDateEnd": "2026-09-15T18:00:00+03:00",
    "summ": 150000,
    "isSumVisible": True,
    "status": "Прием заявок",
    "state": "Published",
}


@pytest.mark.unit
def test_map_procedure_row() -> None:
    row = roseltorg.map_procedure_row(_SAMPLE)
    assert row["tender_id"] == "32616262401"
    assert "ультразвук" in row["title"].lower()
    assert row["customer_name"]
    assert row["deadline_msk"] and row["deadline_msk"].startswith("2026-09-15")
    assert row["price_rub"] == "150000"
    assert "32616262401" in row["url"]
    assert row["source_platform_id"] == PLATFORM_ROSELTORG


@pytest.mark.unit
def test_map_hides_sum_when_not_visible() -> None:
    raw = dict(_SAMPLE, isSumVisible=False)
    row = roseltorg.map_procedure_row(raw)
    assert row["price_rub"] is None


@pytest.mark.unit
def test_open_acceptance_filter() -> None:
    today = date(2026, 8, 28)
    assert roseltorg.is_open_acceptance(_SAMPLE, today=today) is True
    closed = dict(_SAMPLE, acceptanceApplicationsDateEnd="2026-08-01T12:00:00+03:00")
    assert roseltorg.is_open_acceptance(closed, today=today) is False
    undated = {"name": "x"}
    assert roseltorg.is_open_acceptance(undated, today=today) is True


@pytest.mark.unit
def test_prefix_roseltorg() -> None:
    rows = prefix_rows([{"tender_id": "99", "title": "x"}], PLATFORM_ROSELTORG)
    assert rows[0]["tender_id"] == "roseltorg:99"
    assert compose_tender_id(PLATFORM_ROSELTORG, "1") == "roseltorg:1"


@pytest.mark.unit
def test_parse_card_payload() -> None:
    parsed = roseltorg.parse_card_payload(
        {
            "id": 1,
            "name": "Карточка НК",
            "organizator": "АО Заказчик",
            "acceptanceApplicationsDateEnd": "2026-10-01T10:00:00+03:00",
            "description": "ВИК и УЗК сварных швов",
            "lots": [{"name": "Лот 1 контроль"}],
        }
    )
    assert parsed["card_fetched"] is True
    assert "ВИК" in (parsed.get("fit_extra") or "")
    assert parsed.get("doc_links") == []


@pytest.mark.unit
def test_scrape_queries_union_open_dedup(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, int]] = []

    def fake_page(*, query: str, offset: int = 0, **_kw: object):
        calls.append((query, offset))
        if offset > 0:
            return [], 0
        if query == "ВИК":
            return [
                {
                    "id": 1,
                    "name": "ВИК контроль",
                    "acceptanceApplicationsDateEnd": "2026-09-01T00:00:00+03:00",
                }
            ], 1
        return [
            {
                "id": 1,
                "name": "dup",
                "acceptanceApplicationsDateEnd": "2026-09-01T00:00:00+03:00",
            },
            {
                "id": 2,
                "name": "поставка прибора",
                "acceptanceApplicationsDateEnd": "2026-09-01T00:00:00+03:00",
            },
            {
                "id": 3,
                "name": "услуги НК",
                "acceptanceApplicationsDateEnd": "2020-01-01T00:00:00+03:00",
            },
        ], 3

    monkeypatch.setattr(roseltorg, "fetch_procedures_page", fake_page)
    monkeypatch.setattr(roseltorg, "obtain_corp_bearer", lambda *_a, **_k: "tok")
    rows = roseltorg.scrape_queries(
        queries=["ВИК", "НК"],
        limit=10,
        exclude=["поставка"],
        today=date(2026, 8, 28),
        bearer_token="tok",
        delay_s=0,
    )
    assert [r["tender_id"] for r in rows] == ["1"]


@pytest.mark.unit
def test_roseltorg_seeds_gated() -> None:
    off = [r for r in search_seed_rows(roseltorg_in_queue=False) if r["platform_id"] == "roseltorg"]
    on = [r for r in search_seed_rows(roseltorg_in_queue=True) if r["platform_id"] == "roseltorg"]
    assert len(off) == 4
    assert all(r["in_queue"] is False for r in off)
    assert all(r["in_queue"] is True for r in on)
    assert off[0]["name"].startswith("Росэлторг")

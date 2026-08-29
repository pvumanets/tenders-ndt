"""Unit: Росэлторг www mapping, open-filter, docs, twin helpers (no live network)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from app.worker import etp_twins, roseltorg
from app.worker.platform_ids import PLATFORM_ROSELTORG, compose_tender_id, prefix_rows
from app.worker.search_seeds import search_seed_rows

_CARD_HTML = """
<div class="search-results__item js-etp-procedure-grid-item"
     data-feature-favorite-lots-procedure-number="ATOM28082600172">
  <a class="search-results__link search-results__link--description js-etp-procedure-grid-procedure-link"
     href="/procedure/ATOM28082600172/1">мониторинг цен на капиллярный контроль</a>
  <a class="search-results__link js-etp-procedure-grid-procedure-link"
     href="/procedure/ATOM28082600172/1">ATOM28082600172 (Лот 1)</a>
  <div class="search-results__region"><p class="search-results__tooltip">24. Красноярский край</p></div>
  <div class="search-results__customer">
    <a href="/companies/resolve/1">ООО Тест СМУ</a>
  </div>
  <div class="search-results__status status__icon--acceptance">Прием заявок 10 дн.</div>
  <div class="search-results__sum"><p class="desktop">0<sub>,00</sub> ₽</p></div>
</div>
"""

_PROC_HTML = """
<html><body>
<h1>Процедура: ATOM28082600172</h1>
<a class="lot-composition__lot-title" href="/procedure/ATOM28082600172/1">
  капиллярный метод контроля сварных соединений
</a>
<div class="lot-composition-status">Прием заявок 10 дн.</div>
<div class="lot-common-info__row">
  <div class="lot-common-info__text">Приём заявок</div>
  <div class="lot-common-info__value">до 08.09.26 23:59 (МСК)</div>
</div>
<div class="lot-docs" id="documents">
  <ul class="lot-docs__list">
    <a href="https://com.roseltorg.ru/file/get/t/LotDocuments/id/1/name/tz.docx">ТЗ.docx</a>
  </ul>
</div>
</body></html>
"""


@pytest.mark.unit
def test_map_search_card() -> None:
    node = BeautifulSoup(_CARD_HTML, "html.parser").select_one(".js-etp-procedure-grid-item")
    row = roseltorg.map_search_card(node)
    assert row is not None
    assert row["tender_id"] == "ATOM28082600172"
    assert "капилляр" in row["title"].lower()
    assert row["customer_name"]
    assert "Красноярский" in (row.get("location") or "")
    assert "ATOM28082600172" in row["url"]
    assert row["source_platform_id"] == PLATFORM_ROSELTORG
    assert row["etp_procedure_id"] == "ATOM28082600172"


@pytest.mark.unit
def test_open_acceptance_filter() -> None:
    today = date(2026, 8, 29)
    assert (
        roseltorg.is_open_acceptance(
            {"deadline_msk": "08.09.2026", "status": "Прием заявок"}, today=today
        )
        is True
    )
    assert (
        roseltorg.is_open_acceptance(
            {"deadline_msk": "01.08.2026", "status": "Прием заявок"}, today=today
        )
        is False
    )
    assert (
        roseltorg.is_open_acceptance({"status": "Прием заявок 10 дн."}, today=today) is True
    )
    assert roseltorg.is_open_acceptance({"status": "Работа комиссии"}, today=today) is False


@pytest.mark.unit
def test_prefix_roseltorg() -> None:
    rows = prefix_rows([{"tender_id": "ATOM28082600172", "title": "x"}], PLATFORM_ROSELTORG)
    assert rows[0]["tender_id"] == "roseltorg:ATOM28082600172"
    assert compose_tender_id(PLATFORM_ROSELTORG, "ATOM1") == "roseltorg:ATOM1"


@pytest.mark.unit
def test_parse_card_html_docs_and_deadline() -> None:
    parsed = roseltorg.parse_card_html(
        _PROC_HTML, page_url="https://www.roseltorg.ru/procedure/ATOM28082600172/1"
    )
    assert parsed["card_fetched"] is True
    assert parsed["deadline_msk"] == "08.09.2026"
    assert parsed["doc_links"]
    assert "file/get" in parsed["doc_links"][0]["url"]
    assert "капилляр" in (parsed.get("fit_extra") or "").lower()


@pytest.mark.unit
def test_parse_card_payload() -> None:
    parsed = roseltorg.parse_card_payload(
        {
            "id": "ATOM1",
            "name": "Карточка НК",
            "organizator": "АО Заказчик",
            "acceptanceApplicationsDateEnd": "2026-10-01T10:00:00+03:00",
            "description": "ВИК и УЗК сварных швов",
            "lots": [{"name": "Лот 1 контроль"}],
            "doc_links": [{"name": "a.pdf", "url": "https://example/a.pdf"}],
        }
    )
    assert parsed["card_fetched"] is True
    assert "ВИК" in (parsed.get("fit_extra") or "")
    assert parsed["doc_links"][0]["name"] == "a.pdf"


@pytest.mark.unit
def test_scrape_queries_union_open_dedup(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, int]] = []

    def fake_page(*, query: str, page: int, **_kwargs):
        calls.append((query, page))
        if page > 0:
            return []
        if query == "a":
            return [
                {
                    "tender_id": "ATOM1",
                    "title": "open",
                    "url": "https://www.roseltorg.ru/procedure/ATOM1/1",
                    "status": "Прием заявок",
                    "deadline_msk": "15.09.2026",
                    "source_platform_id": PLATFORM_ROSELTORG,
                },
                {
                    "tender_id": "ATOM2",
                    "title": "closed",
                    "url": "https://www.roseltorg.ru/procedure/ATOM2/1",
                    "status": "Завершена",
                    "deadline_msk": "01.08.2026",
                    "source_platform_id": PLATFORM_ROSELTORG,
                },
            ]
        return [
            {
                "tender_id": "ATOM1",
                "title": "dup",
                "url": "https://www.roseltorg.ru/procedure/ATOM1/1",
                "status": "Прием заявок",
                "deadline_msk": "15.09.2026",
                "source_platform_id": PLATFORM_ROSELTORG,
            },
            {
                "tender_id": "COM9",
                "title": "exclude me поставка",
                "url": "https://www.roseltorg.ru/procedure/COM9/1",
                "status": "Прием заявок",
                "deadline_msk": "20.09.2026",
                "source_platform_id": PLATFORM_ROSELTORG,
            },
        ]

    monkeypatch.setattr(roseltorg, "fetch_search_page", fake_page)
    monkeypatch.setattr(roseltorg, "_cookie_dict", lambda *_a, **_k: {"elk": "x"})
    rows = roseltorg.scrape_queries(
        queries=["a", "b"],
        exclude=["поставка"],
        today=date(2026, 8, 29),
        delay_s=0,
    )
    ids = {r["tender_id"] for r in rows}
    assert ids == {"ATOM1"}
    assert ("a", 0) in calls and ("b", 0) in calls


@pytest.mark.unit
def test_seeds_gate_cookies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    jar = tmp_path / "cookies.roseltorg.txt"
    jar.write_text(
        "# Netscape\n.roseltorg.ru\tTRUE\t/\tFALSE\t0\telk\tx\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ROSELTORG_COOKIES_FILE", str(jar))
    assert roseltorg.cookies_present() is True
    rows = search_seed_rows(roseltorg_in_queue=True)
    re_rows = [r for r in rows if r["platform_id"] == PLATFORM_ROSELTORG]
    assert len(re_rows) == 5
    assert all(r["in_queue"] for r in re_rows)


@pytest.mark.unit
def test_extract_etp_procedure_id() -> None:
    assert etp_twins.extract_etp_procedure_id("ЕЭТП ATOM28082600172") == "ATOM28082600172"
    assert etp_twins.extract_etp_procedure_id("https://x/COM10082600005") == "COM10082600005"

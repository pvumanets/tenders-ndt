"""Unit: B2B-Center HTML parsers and helpers (no live HTTP)."""
from __future__ import annotations

import pytest

from app.worker import b2b_center
from app.worker import rts_market
from app.worker.platform_ids import PLATFORM_B2B_CENTER, compose_tender_id, prefix_rows

_LIST_HTML = """
<html><body>
<table class="table table-hover search-results">
<tbody>
<tr>
  <td><a class="search-results-title" href="/app/market/instrumenty/tender-4580345/">
    Запрос предложений № 4580345 Инструменты Набор ВИК
  </a></td>
  <td><a href="/firms/ao-tatnefteprovodstroi/255286/">АО Татнефтепроводстрой</a></td>
</tr>
<tr>
  <td><a class="search-results-title" href="/market/view.html?id=4576052">
    Запрос предложений № 4576052 Ремонт установок дефектоскопии
  </a></td>
  <td>Прием заявок до: 15.09.2026 18:00</td>
</tr>
</tbody>
</table>
</body></html>
"""

_CARD_HTML = """
<html><head><title>Ремонт установок дефектоскопии — ООО ТН-Сервис — B2B-Center</title></head>
<body>
<h1>Запрос предложений № 4576052</h1>
<div>Организатор:</div>
<div>ООО "ТН-Сервис"</div>
<div>Дата окончания приема заявок: 15.09.2026 18:00</div>
<a href="/file/download/123.pdf">ТЗ.pdf</a>
<p>Ремонт и обслуживание установок дефектоскопии (неразрушающего контроля).</p>
</body></html>
"""


@pytest.mark.unit
def test_card_url_canonical() -> None:
    assert b2b_center.card_url("4576052") == (
        "https://www.b2b-center.ru/market/view.html?id=4576052"
    )


@pytest.mark.unit
def test_list_query_params_trade_buy() -> None:
    params = b2b_center.list_query_params("ВИК")
    assert params["f_keyword"] == "ВИК"
    assert params["searching"] == "1"
    assert params["trade"] == "buy"
    assert "page" not in params
    assert b2b_center.list_query_params("x", page=2)["page"] == "2"


@pytest.mark.unit
def test_parse_list_html() -> None:
    rows = b2b_center.parse_list_html(_LIST_HTML)
    assert len(rows) == 2
    assert rows[0].tender_id == "4580345"
    assert rows[0].url.endswith("/market/view.html?id=4580345")
    assert rows[0].customer_name and "Татнефтепроводстрой" in rows[0].customer_name
    assert rows[1].tender_id == "4576052"
    assert rows[1].deadline_msk == "15.09.2026 18:00"


@pytest.mark.unit
def test_parse_card_html() -> None:
    parsed = b2b_center.parse_card_html(_CARD_HTML)
    assert "4576052" in (parsed.get("title") or "")
    assert parsed.get("deadline_msk") == "15.09.2026 18:00"
    assert parsed.get("customer_name") and "ТН-Сервис" in parsed["customer_name"]
    assert any("tz.pdf" in d["url"].lower() or "123.pdf" in d["url"] for d in parsed["doc_links"])


@pytest.mark.unit
def test_prefix_rows_b2b() -> None:
    rows = prefix_rows([{"tender_id": "4576052", "title": "x"}], PLATFORM_B2B_CENTER)
    assert rows[0]["tender_id"] == "b2b-center:4576052"
    assert rows[0]["source_platform_id"] == PLATFORM_B2B_CENTER
    assert compose_tender_id(PLATFORM_B2B_CENTER, "1") == "b2b-center:1"
    assert b2b_center.prefixed_compose("9") == "b2b-center:9"


@pytest.mark.unit
def test_scrape_queries_dedup(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_page(
        site,
        *,
        keyword: str,
        base=None,
        page: int = 1,
        client=None,
        cookies_file=None,
        on_retry=None,
    ):
        calls.append(keyword)
        if keyword == "ВИК":
            return (
                [
                    {
                        "tender_id": "1",
                        "title": "a",
                        "url": "https://www.b2b-center.ru/market/view.html?id=1",
                    }
                ],
                None,
            )
        return (
            [
                {
                    "tender_id": "1",
                    "title": "dup",
                    "url": "https://www.b2b-center.ru/market/view.html?id=1",
                },
                {
                    "tender_id": "2",
                    "title": "b",
                    "url": "https://www.b2b-center.ru/market/view.html?id=2",
                },
            ],
            None,
        )

    monkeypatch.setattr(rts_market, "scrape_list_page", fake_page)
    monkeypatch.setattr(rts_market, "_cookie_dict", lambda site, path=None: {})
    rows = b2b_center.scrape_queries(queries=["ВИК", "УЗК"], delay_s=0)
    assert [r["tender_id"] for r in rows] == ["1", "2"]
    assert calls == ["ВИК", "УЗК"]

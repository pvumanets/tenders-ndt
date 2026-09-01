"""Unit: RTS Rosatom HTML parsers and helpers (no live HTTP)."""
from __future__ import annotations

import pytest

from app.worker import rts_market
from app.worker import rts_rosatom
from app.worker.platform_ids import PLATFORM_RTS_ROSATOM, compose_tender_id, prefix_rows

_LIST_HTML = """
<html><body>
<table class="table table-hover search-results">
<tbody>
<tr>
  <td><a class="search-results-title" href="/market/view.html?id=9001">
    Запрос предложений № 9001 Неразрушающий контроль сварных швов
  </a></td>
  <td>АО Концерн Росэнергоатом</td>
  <td>Прием заявок до: 20.10.2026 12:00</td>
</tr>
</tbody>
</table>
</body></html>
"""

_CARD_HTML = """
<html><head><title>НК сварных швов — Росатом — RTS</title></head>
<body>
<h1>Запрос предложений № 9001</h1>
<div>Организатор:</div>
<div>АО Концерн Росэнергоатом</div>
<div>Дата окончания приема заявок: 20.10.2026 12:00</div>
<p>Услуги неразрушающего контроля.</p>
</body></html>
"""


@pytest.mark.unit
def test_card_url_rosatom() -> None:
    assert rts_rosatom.card_url("9001") == (
        "https://www.rosatom.rts-tender.ru/market/view.html?id=9001"
    )


@pytest.mark.unit
def test_parse_list_html() -> None:
    rows = rts_rosatom.parse_list_html(_LIST_HTML)
    assert len(rows) == 1
    assert rows[0].tender_id == "9001"
    assert "9001" in rows[0].url
    assert rows[0].deadline_msk == "20.10.2026 12:00"


@pytest.mark.unit
def test_parse_card_html() -> None:
    parsed = rts_rosatom.parse_card_html(_CARD_HTML)
    assert "9001" in (parsed.get("title") or "")
    assert parsed.get("deadline_msk") == "20.10.2026 12:00"


@pytest.mark.unit
def test_prefix_rows_rts() -> None:
    rows = prefix_rows([{"tender_id": "9001", "title": "x"}], PLATFORM_RTS_ROSATOM)
    assert rows[0]["tender_id"] == "rts-rosatom:9001"
    assert compose_tender_id(PLATFORM_RTS_ROSATOM, "1") == "rts-rosatom:1"


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
                        "url": "https://www.rosatom.rts-tender.ru/market/view.html?id=1",
                    }
                ],
                None,
            )
        return (
            [
                {
                    "tender_id": "1",
                    "title": "dup",
                    "url": "https://www.rosatom.rts-tender.ru/market/view.html?id=1",
                },
                {
                    "tender_id": "2",
                    "title": "b",
                    "url": "https://www.rosatom.rts-tender.ru/market/view.html?id=2",
                },
            ],
            None,
        )

    monkeypatch.setattr(rts_market, "scrape_list_page", fake_page)
    monkeypatch.setattr(rts_market, "_cookie_dict", lambda site, path=None: {})
    rows = rts_rosatom.scrape_queries(queries=["ВИК", "УЗК"], delay_s=0)
    assert [r["tender_id"] for r in rows] == ["1", "2"]
    assert calls == ["ВИК", "УЗК"]

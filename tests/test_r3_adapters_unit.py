"""Unit: R3 adapter fixtures (084) + scrape log redact (086)."""
from __future__ import annotations

import logging
from datetime import date

import pytest

from bs4 import BeautifulSoup

from app.worker import b2b_center, oilb2bcs, roseltorg, rts_market, tender_pro
from app.worker.list_scrape import page_list_url
from app.worker.scrape_log import log_fetch, redact_url


@pytest.mark.unit
def test_page_list_url_keeps_question_when_page_is_only_param() -> None:
    assert page_list_url("https://rostender.info/search?page=1", 2) == (
        "https://rostender.info/search?page=2"
    )
    assert page_list_url("https://rostender.info/search?q=vik&page=1", 3) == (
        "https://rostender.info/search?q=vik&page=3"
    )
    assert page_list_url("https://rostender.info/search", 2) == (
        "https://rostender.info/search?page=2"
    )


@pytest.mark.unit
def test_roseltorg_acceptance_completed_is_closed() -> None:
    today = date(2026, 8, 29)
    assert (
        roseltorg.is_open_acceptance(
            {"status": "Прием заявок завершен"}, today=today
        )
        is False
    )
    assert (
        roseltorg.is_open_acceptance(
            {"status": "Приём заявок окончен"}, today=today
        )
        is False
    )
    assert (
        roseltorg.is_open_acceptance({"status": "Прием заявок 10 дн."}, today=today)
        is True
    )


@pytest.mark.unit
def test_tender_pro_continues_when_empty_parse_but_total_remains(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    def fake_page(*, good_name: str, page: int = 1, **_kw: object):
        del good_name
        calls.append(page)
        if page == 1:
            return [], 50
        if page == 2:
            return [{"tender_id": "9", "title": "УЗК", "url": "https://x/9"}], 50
        return [], 50

    monkeypatch.setattr(tender_pro, "scrape_list_page", fake_page)
    rows = tender_pro.scrape_queries(queries=["ВИК"], limit=0, delay_s=0)
    assert [row["tender_id"] for row in rows] == ["9"]
    assert 1 in calls and 2 in calls


@pytest.mark.unit
def test_rts_paginates_per_query_when_ids_already_in_union(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_page(site, *, keyword: str, page: int = 1, **_kw: object):
        del site
        nxt = BeautifulSoup(f'<a href="?page={page + 1}">далее</a>', "html.parser")
        if keyword == "ВИК":
            if page == 1:
                return (
                    [
                        {"tender_id": "1", "title": "a", "url": "https://x/1"},
                        {"tender_id": "2", "title": "b", "url": "https://x/2"},
                    ],
                    nxt,
                )
            return ([{"tender_id": "3", "title": "c", "url": "https://x/3"}], None)
        if page == 1:
            return (
                [
                    {"tender_id": "1", "title": "dup", "url": "https://x/1"},
                    {"tender_id": "2", "title": "dup2", "url": "https://x/2"},
                ],
                nxt,
            )
        return ([{"tender_id": "4", "title": "d", "url": "https://x/4"}], None)

    monkeypatch.setattr(rts_market, "scrape_list_page", fake_page)
    monkeypatch.setattr(rts_market, "_cookie_dict", lambda site, path=None: {})
    rows = b2b_center.scrape_queries(queries=["ВИК", "УЗК"], delay_s=0)
    assert [row["tender_id"] for row in rows] == ["1", "2", "3", "4"]


@pytest.mark.unit
def test_oilb2b_api_v1_inside_string_does_not_break_parse() -> None:
    body = (
        '{result:[1,[{"Id":9,"CategoryText":"НК","CustomerText":"ООО",'
        '"Stop":"2026-09-15T10:00:00.000","State":"Открыта",'
        '"Note":"API: v1, word: keep"}],'
        '[{"planclaim":9,"name":"ВИК"}]]}'
    )
    parsed = oilb2bcs._parse_extnet_payload(body)
    assert parsed[0] == 1
    assert parsed[1][0]["Id"] == 9
    assert parsed[1][0]["Note"] == "API: v1, word: keep"
    assert parsed[2][0]["name"] == "ВИК"


@pytest.mark.unit
def test_log_fetch_redacts_cookie_query_and_keeps_url_on_zero_rows(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="scout.worker")
    secret = "SECRETCOOKIEVALUE"
    url = f"https://etp.example/search?cookie={secret}&q=vik"
    log_fetch(platform="rostender", url=url, status=200, parsed_n=0)
    text = caplog.text
    assert secret not in text
    assert "REDACTED" in text
    assert "parsed_n=0" in text
    assert "status=200" in text
    assert "etp.example/search" in redact_url(url)

"""Unit: Rostender published_msk «от DD.MM.YY» from card HTML."""
from __future__ import annotations

import pytest

from app.worker.card_scrape import parse_card_html, parse_published_msk
from app.worker.list_scrape import parse_list_published
from bs4 import BeautifulSoup


@pytest.mark.unit
def test_parse_published_msk_from_header_ot_short_year() -> None:
    html = """
    <html><body>
      <h1>№94734024 от 02.09.26 Выполнение работ по НК</h1>
      <div>Окончание (МСК)</div><div>09.09.2026 10:00</div>
    </body></html>
    """
    assert parse_published_msk(html) == "02.09.26"
    fields = parse_card_html(html, title_hint="НК")
    assert fields["published_msk"] == "02.09.26"
    assert fields["deadline_msk"] == "09.09.2026 10:00" or fields["deadline_msk"] == "09.09.2026"


@pytest.mark.unit
def test_parse_published_msk_full_year() -> None:
    html = "<html><body><div class='tender-header'>Тендер от 02.09.2026</div></body></html>"
    assert parse_published_msk(html) == "02.09.2026"


@pytest.mark.unit
def test_parse_list_published_dtstart() -> None:
    art = BeautifulSoup(
        '<article class="tender-row"><span class="dtstart">2026-09-02</span>'
        '<span class="dtend">2026-09-09</span></article>',
        "lxml",
    ).select_one("article")
    assert parse_list_published(art) == "02.09.2026"

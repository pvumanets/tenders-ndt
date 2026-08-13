"""Unit: P1 keeps only open/upcoming lots from list HTML."""
from __future__ import annotations

from datetime import datetime

import pytest

from app.worker.list_scrape import MSK, _parse_rows, is_open_upcoming
from bs4 import BeautifulSoup

_HTML = """
<html><body>
<article class="tender-row">
  <a href="/region/x/111-tender-open">УЗК открытый</a>
  <div class="location">Москва</div>
  <div class="dtend">2026-08-20 00:00:00</div>
  <div class="tender__countdown-text">Окончание (МСК) 20.08.2026</div>
  Приём заявок
</article>
<article class="tender-row">
  <a href="/region/x/222-tender-past">УЗК прошлый</a>
  <div class="dtend">2026-07-01 00:00:00</div>
  Приём заявок
</article>
<article class="tender-row">
  <a href="/region/x/333-tender-closed">УЗК закрытый</a>
  <div class="dtend">2026-08-20 00:00:00</div>
  Завершён
</article>
</body></html>
"""


@pytest.mark.unit
def test_parse_rows_drops_past_and_closed() -> None:
    now = datetime(2026, 8, 13, 12, 0, tzinfo=MSK)
    rows = _parse_rows(_HTML, "https://rostender.info", now=now)
    assert [r.tender_id for r in rows] == ["111"]
    assert rows[0].deadline_msk == "20.08.2026"
    assert rows[0].status == "Приём заявок"


@pytest.mark.unit
def test_is_open_upcoming_deadline_today_inclusive() -> None:
    html = """
    <article class="tender-row">
      <a href="/region/x/1-tender-x">x</a>
      <div class="dtend">2026-08-13 00:00:00</div>
    </article>
    """
    art = BeautifulSoup(html, "lxml").select_one("article.tender-row")
    now = datetime(2026, 8, 13, 18, 0, tzinfo=MSK)
    assert is_open_upcoming(art, now=now) is True
    later = datetime(2026, 8, 14, 0, 0, tzinfo=MSK)
    assert is_open_upcoming(art, now=later) is False

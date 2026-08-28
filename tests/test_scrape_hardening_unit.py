"""Unit: P14/031 re-score, pagination meta, probe helpers."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.scoring.pipeline import rescore_rows, score_rows
from app.worker.list_scrape import MAX_FILTERED_EMPTY_PAGES, _parse_rows_meta, probe_rostender_cookies


_HTML_MIXED = """
<html><body>
<article class="tender-row">
  <a href="/region/x/111-tender-open">УЗК открытый</a>
  <div class="dtend">2026-08-20 00:00:00</div>
  Приём заявок
</article>
<article class="tender-row">
  <a href="/region/x/222-tender-past">УЗК прошлый</a>
  <div class="dtend">2026-07-01 00:00:00</div>
  Приём заявок
</article>
</body></html>
"""


@pytest.mark.unit
def test_parse_rows_meta_distinguishes_raw_from_filtered() -> None:
    from datetime import datetime

    from app.worker.list_scrape import MSK

    now = datetime(2026, 8, 13, 12, 0, tzinfo=MSK)
    rows, raw_count = _parse_rows_meta(_HTML_MIXED, "https://rostender.info", now=now)
    assert raw_count == 2
    assert len(rows) == 1
    assert rows[0].tender_id == "111"


@pytest.mark.unit
def test_filtered_empty_streak_constant() -> None:
    assert MAX_FILTERED_EMPTY_PAGES >= 2


@pytest.mark.unit
def test_rescore_promotes_when_methods_present() -> None:
    base = [{"tender_id": "1", "title": "Мебель офисная", "rank": 1}]
    scored, _, _ = score_rows(base)
    title_only_tier = scored[0]["tier"]
    row = dict(scored[0])
    row["card_fetched"] = True
    row["methods"] = "ВИК"
    rescored, _, card_ids = rescore_rows([row])
    assert rescored[0]["tier"] in {"L1", "L2", "L3", "noise", "pool"}
    assert rescored[0]["score"] >= scored[0]["score"]
    if title_only_tier in {"noise", "pool"}:
        assert rescored[0]["tier"] in {"L1", "L2", "L3"} or rescored[0]["score"] > scored[0]["score"]
    if rescored[0]["tier"] in {"L1", "L2", "L3"}:
        assert rescored[0]["tender_id"] in card_ids


@pytest.mark.unit
def test_probe_rostender_missing_file(tmp_path: Path) -> None:
    assert probe_rostender_cookies(tmp_path / "missing.txt") == "missing"


@pytest.mark.unit
def test_probe_rostender_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "cookies.txt"
    path.write_text("", encoding="utf-8")
    assert probe_rostender_cookies(path) == "missing"

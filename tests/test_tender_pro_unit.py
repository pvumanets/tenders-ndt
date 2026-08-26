"""Unit: Tender.Pro HTML parsers and platform id helpers (no live HTTP)."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.worker import tender_pro
from app.worker.platform_ids import (
    PLATFORM_ROSTENDER,
    PLATFORM_TENDER_PRO,
    compose_tender_id,
    ensure_prefixed,
    prefix_rows,
    rename_legacy_docs_dirs,
    volume_dir_name,
)

_LIST_HTML = """
<html><body>
<div>(всего строк: 2)</div>
<table>
<tr class="table-stat__row">
  <td>1227021</td>
  <td><a href="/api/tender/1227021/view_public">Мебель офисная</a></td>
  <td>Прием заявок до: 16.08.2026 18:00</td>
</tr>
<tr class="table-stat__row">
  <td>1229169</td>
  <td><a href="/api/tender/1229169/view_public">Закупка приборов КИП</a></td>
  <td>Прием заявок до: 21.08.2026 13:00</td>
</tr>
</table>
</body></html>
"""

_CARD_HTML = """
<html><body>
<h1>Мебель офисная</h1>
<div>Прием заявок до: 16.08.2026 18:00 MSK</div>
<div>Открыт</div>
<h2>Товары</h2>
<div>ВИК контроль сварных швов</div>
<h2>Документы</h2>
<a href="/files/tz.pdf">ТЗ.pdf</a>
</body></html>
"""


@pytest.mark.unit
def test_compose_and_volume_dir() -> None:
    assert compose_tender_id("rostender", "45289101") == "rostender:45289101"
    assert volume_dir_name("rostender:45289101") == "rostender__45289101"
    assert volume_dir_name("tender-pro:1227021") == "tender-pro__1227021"
    assert ensure_prefixed("45289101", PLATFORM_ROSTENDER) == "rostender:45289101"
    assert ensure_prefixed("rostender:1", PLATFORM_ROSTENDER) == "rostender:1"


@pytest.mark.unit
def test_prefix_rows() -> None:
    rows = prefix_rows([{"tender_id": "99", "title": "x"}], PLATFORM_TENDER_PRO)
    assert rows[0]["tender_id"] == "tender-pro:99"
    assert rows[0]["source_platform_id"] == PLATFORM_TENDER_PRO


@pytest.mark.unit
def test_rename_legacy_docs_dirs(tmp_path: Path) -> None:
    old = tmp_path / "45289101"
    old.mkdir()
    (old / "a.pdf").write_bytes(b"%PDF")
    assert rename_legacy_docs_dirs(tmp_path) == 1
    assert (tmp_path / "rostender__45289101" / "a.pdf").is_file()
    assert not old.exists()
    assert rename_legacy_docs_dirs(tmp_path) == 0


@pytest.mark.unit
def test_rename_legacy_docs_dirs_missing_root(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    assert rename_legacy_docs_dirs(missing) == 0


@pytest.mark.unit
def test_parse_list_html() -> None:
    rows, total = tender_pro.parse_list_html(_LIST_HTML)
    assert total == 2
    assert [r.tender_id for r in rows] == ["1227021", "1229169"]
    assert "view_public" in rows[0].url
    assert rows[0].deadline_msk and "16.08.2026" in rows[0].deadline_msk


@pytest.mark.unit
def test_parse_card_html() -> None:
    parsed = tender_pro.parse_card_html(_CARD_HTML)
    assert "Мебель" in (parsed.get("title") or "")
    assert parsed.get("deadline_msk")
    assert parsed.get("doc_links")
    assert any("tz.pdf" in (link.get("url") or "") for link in parsed["doc_links"])


@pytest.mark.unit
def test_scrape_queries_union(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, int]] = []

    def fake_page(*, good_name: str, page: int = 1, **_kw: object):
        calls.append((good_name, page))
        if page > 1:
            return [], 1
        if good_name == "ВИК":
            return [{"tender_id": "1", "title": "a", "url": "https://x/1"}], 1
        return [{"tender_id": "1", "title": "dup", "url": "https://x/1"}, {"tender_id": "2", "title": "b", "url": "https://x/2"}], 2

    monkeypatch.setattr(tender_pro, "scrape_list_page", fake_page)
    rows = tender_pro.scrape_queries(queries=["ВИК", "РК"], limit=10)
    assert [r["tender_id"] for r in rows] == ["1", "2"]

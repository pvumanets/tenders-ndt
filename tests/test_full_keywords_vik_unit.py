"""Unit: 034 — Rostender seeds full phrases; VIK only abbreviation."""
from __future__ import annotations

import pytest

from app.worker.search_seeds import search_seed_rows

_FORBIDDEN_RT = {
    "нераз.",
    "дефект.",
    "ультр.",
    "визуал.",
    "капиляр.",
    "радиогр.",
    "гамма.",
    "прин.",
    "контроль сварн",
    "диагностирование",
    "техническое диагностирование",
    "НК",
    "УЗК",
    "ПВК",
}


@pytest.mark.unit
def test_rostender_no_truncations_or_abbr_except_vik() -> None:
    rt = [r for r in search_seed_rows() if r["platform_id"] == "rostender"]
    all_queries: list[str] = []
    for row in rt:
        all_queries.extend(row["queries"])
    assert "ВИК" in all_queries
    abbr = [q for q in all_queries if q.isupper() and len(q) <= 4]
    assert abbr == ["ВИК"]
    for bad in _FORBIDDEN_RT:
        assert bad not in all_queries


@pytest.mark.unit
def test_rostender_package_e_full_phrases() -> None:
    e = next(r for r in search_seed_rows() if r["name"] == "РосТендер — страховка")
    assert e["queries"] == ["контроль сварных соединений", "сварных соединений"]

"""Unit: 041 — shared A–E packages identical across platforms."""
from __future__ import annotations

import pytest

from app.worker.search_seeds import search_seed_rows

_FORBIDDEN = {
    "нераз.",
    "дефект.",
    "контроль сварн",
    "диагностирование",
    "НК",
    "УЗК",
    "ПВК",
}

_LEVEL_SUFFIXES = (
    "услуги НК",
    "методы",
    "аббревиатуры",
    "контроли",
    "страховка",
)


def _by_platform(platform_id: str) -> list[dict]:
    return [r for r in search_seed_rows() if r["platform_id"] == platform_id]


@pytest.mark.unit
def test_all_platforms_have_a_to_e() -> None:
    for platform_id, prefix in (
        ("rostender", "РосТендер"),
        ("tender-pro", "Tender.Pro"),
        ("roseltorg", "Росэлторг"),
    ):
        rows = _by_platform(platform_id)
        assert len(rows) == 5
        assert [r["name"] for r in rows] == [f"{prefix} — {s}" for s in _LEVEL_SUFFIXES]


@pytest.mark.unit
def test_queries_and_exclude_match_across_platforms() -> None:
    rt = _by_platform("rostender")
    for other_id in ("tender-pro", "roseltorg"):
        other = _by_platform(other_id)
        for a, b in zip(rt, other, strict=True):
            assert a["queries"] == b["queries"], (a["name"], b["name"])
            assert a["exclude"] == b["exclude"], (a["name"], b["name"])


@pytest.mark.unit
def test_no_forbidden_queries_on_any_platform() -> None:
    for row in search_seed_rows():
        for q in row["queries"]:
            assert q not in _FORBIDDEN
            if q.isupper() and len(q) <= 4:
                assert q == "ВИК"


@pytest.mark.unit
def test_package_c_vik_only() -> None:
    for row in search_seed_rows():
        if row["name"].endswith("— аббревиатуры"):
            assert row["queries"] == ["ВИК"]


@pytest.mark.unit
def test_package_e_full_weld_phrases() -> None:
    for row in search_seed_rows():
        if row["name"].endswith("— страховка"):
            assert row["queries"] == [
                "контроль сварных соединений",
                "сварных соединений",
            ]


@pytest.mark.unit
def test_package_d_has_construction_and_social_exclude() -> None:
    for row in search_seed_rows():
        if not row["name"].endswith("— контроли"):
            continue
        assert "строительный контроль" in row["queries"]
        for phrase in ("кровля", "детсад", "поставка"):
            assert phrase in row["exclude"]

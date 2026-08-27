"""Canonical named-search seeds for P11 / task 030 (search-keywords.md)."""
from __future__ import annotations

from typing import Any
from uuid import UUID

# Stable IDs so re-runs / migrations stay idempotent.
_SEED_IDS = {
    "rt-a": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a1"),
    "rt-b": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a2"),
    "rt-c": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a3"),
    "rt-d": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a4"),
    "rt-e": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a5"),
    "tp-methods": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b1"),
    "tp-abbr": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b2"),
    "tp-ctrl": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b3"),
    "tp-insure": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b4"),
}

# Legacy rows from 0003_searches
LEGACY_SEARCH_IDS = (
    UUID("aaaaaaaa-bbbb-4ccc-8ddd-000000000001"),
    UUID("aaaaaaaa-bbbb-4ccc-8ddd-000000000002"),
)

# limit_n=0 → no product cap (soft unlimited)
_DEFAULT_LIMIT = 0


def search_seed_rows(*, tender_pro_in_queue: bool = False) -> list[dict[str, Any]]:
    """Rostender A–E in queue; Tender.Pro packages (queue gated by cookies)."""
    rostender = [
        {
            "id": _SEED_IDS["rt-a"],
            "name": "РосТендер — услуги НК",
            "platform_id": "rostender",
            "queries": [
                "неразрушающий контроль",
                "нераз.",
                "дефектоскопия",
                "дефект.",
            ],
            "limit_n": _DEFAULT_LIMIT,
            "in_queue": True,
            "sort_order": 1,
        },
        {
            "id": _SEED_IDS["rt-b"],
            "name": "РосТендер — методы",
            "platform_id": "rostender",
            "queries": [
                "ультразвуковой контроль",
                "ультр.",
                "визуально-измерительный",
                "визуал.",
                "капиллярный",
                "капиляр.",
                "радиографический",
                "радиогр.",
                "гаммаграфический",
                "гамма.",
                "толщинометрия ультразвуковая",
            ],
            "limit_n": _DEFAULT_LIMIT,
            "in_queue": True,
            "sort_order": 2,
        },
        {
            "id": _SEED_IDS["rt-c"],
            "name": "РосТендер — аббревиатуры",
            "platform_id": "rostender",
            "queries": ["НК", "УК", "ВИК", "ПВК", "РК"],
            "limit_n": _DEFAULT_LIMIT,
            "in_queue": True,
            "sort_order": 3,
        },
        {
            "id": _SEED_IDS["rt-d"],
            "name": "РосТендер — контроли",
            "platform_id": "rostender",
            "queries": [
                "принимающий контроль",
                "прин.",
                "приёмочный контроль",
                "входной контроль",
                "строительный контроль",
            ],
            "limit_n": _DEFAULT_LIMIT,
            "in_queue": True,
            "sort_order": 4,
        },
        {
            "id": _SEED_IDS["rt-e"],
            "name": "РосТендер — страховка",
            "platform_id": "rostender",
            "queries": [
                "контроль сварн",
                "сварных соединений",
                "диагностирование",
                "техническое диагностирование",
            ],
            "limit_n": _DEFAULT_LIMIT,
            "in_queue": True,
            "sort_order": 5,
        },
    ]
    tender_pro = [
        {
            "id": _SEED_IDS["tp-methods"],
            "name": "Tender.Pro — методы",
            "platform_id": "tender-pro",
            "queries": [
                "ультразвуковой контроль",
                "визуально-измерительный",
                "капиллярный",
                "радиографический",
            ],
            "limit_n": _DEFAULT_LIMIT,
            "in_queue": tender_pro_in_queue,
            "sort_order": 10,
        },
        {
            "id": _SEED_IDS["tp-abbr"],
            "name": "Tender.Pro — аббревиатуры",
            "platform_id": "tender-pro",
            "queries": ["ВИК", "ПВК", "УК", "РК", "НК"],
            "limit_n": _DEFAULT_LIMIT,
            "in_queue": tender_pro_in_queue,
            "sort_order": 11,
        },
        {
            "id": _SEED_IDS["tp-ctrl"],
            "name": "Tender.Pro — контроли",
            "platform_id": "tender-pro",
            "queries": [
                "принимающий контроль",
                "приёмочный контроль",
                "входной контроль",
                "строительный контроль",
            ],
            "limit_n": _DEFAULT_LIMIT,
            "in_queue": tender_pro_in_queue,
            "sort_order": 12,
        },
        {
            "id": _SEED_IDS["tp-insure"],
            "name": "Tender.Pro — страховка",
            "platform_id": "tender-pro",
            "queries": ["контроль сварн", "диагностирование"],
            "limit_n": _DEFAULT_LIMIT,
            "in_queue": tender_pro_in_queue,
            "sort_order": 13,
        },
    ]
    return rostender + tender_pro

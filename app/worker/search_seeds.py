"""Canonical named-search seeds — shared A–E packages (Rostender lexicon) for all platforms."""
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
    "tp-a": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b0"),
    "tp-b": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b1"),  # was tp-methods
    "tp-c": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b2"),  # was tp-abbr
    "tp-d": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b3"),  # was tp-ctrl
    "tp-e": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b4"),  # was tp-insure
    "re-a": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000c0"),
    "re-b": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000c1"),  # was re-methods
    "re-c": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000c2"),  # was re-abbr
    "re-d": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000c3"),  # was re-ctrl
    "re-e": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000c4"),  # was re-insure
}

# Legacy rows from 0003_searches
LEGACY_SEARCH_IDS = (
    UUID("aaaaaaaa-bbbb-4ccc-8ddd-000000000001"),
    UUID("aaaaaaaa-bbbb-4ccc-8ddd-000000000002"),
)

# limit_n=0 → no product cap (soft unlimited)
_DEFAULT_LIMIT = 0

# Package D minus (search-system-v2) + supply minus on all packages (037)
_RT_D_EXCLUDE = [
    "жилой",
    "жилых",
    "ЖК",
    "кровля",
    "крыша",
    "ЗАГС",
    "школа",
    "детсад",
    "поликлиника",
    "фасад",
    "благоустройство",
    "дороги",
]
_SUPPLY_EXCLUDE = ["поставка", "закупка", "прибор"]

# Shared A–E lexicon (Rostender canon) — same queries/exclude on every platform.
_PACKAGE_A_QUERIES = [
    "неразрушающий контроль",
    "дефектоскопия",
]
_PACKAGE_B_QUERIES = [
    "ультразвуковой контроль",
    "визуально-измерительный контроль",
    "капиллярный контроль",
    "радиографический контроль",
    "гаммаграфический контроль",
    "толщинометрия ультразвуковая",
]
_PACKAGE_C_QUERIES = ["ВИК"]
_PACKAGE_D_QUERIES = [
    "принимающий контроль",
    "приёмочный контроль",
    "входной контроль",
    "строительный контроль",
]
_PACKAGE_E_QUERIES = [
    "контроль сварных соединений",
    "сварных соединений",
]


def _exclude_supply() -> list[str]:
    return list(_SUPPLY_EXCLUDE)


def _exclude_d_full() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for phrase in _RT_D_EXCLUDE + _SUPPLY_EXCLUDE:
        if phrase not in seen:
            seen.add(phrase)
            out.append(phrase)
    return out


def _shared_packages() -> list[dict[str, Any]]:
    """Ordered A–E package templates (no platform fields)."""
    return [
        {
            "key": "a",
            "suffix": "услуги НК",
            "queries": list(_PACKAGE_A_QUERIES),
            "exclude": _exclude_supply(),
        },
        {
            "key": "b",
            "suffix": "методы",
            "queries": list(_PACKAGE_B_QUERIES),
            "exclude": _exclude_supply(),
        },
        {
            "key": "c",
            "suffix": "аббревиатуры",
            "queries": list(_PACKAGE_C_QUERIES),
            "exclude": _exclude_supply(),
        },
        {
            "key": "d",
            "suffix": "контроли",
            "queries": list(_PACKAGE_D_QUERIES),
            "exclude": _exclude_d_full(),
        },
        {
            "key": "e",
            "suffix": "страховка",
            "queries": list(_PACKAGE_E_QUERIES),
            "exclude": _exclude_supply(),
        },
    ]


def seeds_for_platform(
    *,
    platform_id: str,
    name_prefix: str,
    id_prefix: str,
    sort_base: int,
    in_queue: bool,
) -> list[dict[str, Any]]:
    """Build A–E named searches for one ETP from the shared lexicon."""
    rows: list[dict[str, Any]] = []
    for i, pkg in enumerate(_shared_packages()):
        seed_key = f"{id_prefix}-{pkg['key']}"
        rows.append(
            {
                "id": _SEED_IDS[seed_key],
                "name": f"{name_prefix} — {pkg['suffix']}",
                "platform_id": platform_id,
                "queries": list(pkg["queries"]),
                "exclude": list(pkg["exclude"]),
                "limit_n": _DEFAULT_LIMIT,
                "in_queue": in_queue,
                "sort_order": sort_base + i,
            }
        )
    return rows


def search_seed_rows(
    *,
    tender_pro_in_queue: bool = False,
    roseltorg_in_queue: bool = False,
) -> list[dict[str, Any]]:
    """Shared A–E on rostender / tender-pro / roseltorg; queue gated per platform."""
    return (
        seeds_for_platform(
            platform_id="rostender",
            name_prefix="РосТендер",
            id_prefix="rt",
            sort_base=1,
            in_queue=True,
        )
        + seeds_for_platform(
            platform_id="tender-pro",
            name_prefix="Tender.Pro",
            id_prefix="tp",
            sort_base=10,
            in_queue=tender_pro_in_queue,
        )
        + seeds_for_platform(
            platform_id="roseltorg",
            name_prefix="Росэлторг",
            id_prefix="re",
            sort_base=20,
            in_queue=roseltorg_in_queue,
        )
    )

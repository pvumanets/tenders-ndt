"""Canonical search-group seeds — shared A–E packages (Rostender lexicon)."""
from __future__ import annotations

from typing import Any
from uuid import UUID

# Stable group IDs (048) — one UUID per package A–E.
_GROUP_IDS = {
    "a": UUID("aaaaaaaa-bbbb-4ccc-8eee-0000000000a1"),
    "b": UUID("aaaaaaaa-bbbb-4ccc-8eee-0000000000a2"),
    "c": UUID("aaaaaaaa-bbbb-4ccc-8eee-0000000000a3"),
    "d": UUID("aaaaaaaa-bbbb-4ccc-8eee-0000000000a4"),
    "e": UUID("aaaaaaaa-bbbb-4ccc-8eee-0000000000a5"),
}

# Legacy per-platform seed IDs (pre-048) → group key for migration remap.
_LEGACY_SEED_TO_GROUP_KEY = {
    "rt-a": "a",
    "rt-b": "b",
    "rt-c": "c",
    "rt-d": "d",
    "rt-e": "e",
    "tp-a": "a",
    "tp-b": "b",
    "tp-c": "c",
    "tp-d": "d",
    "tp-e": "e",
    "re-a": "a",
    "re-b": "b",
    "re-c": "c",
    "re-d": "d",
    "re-e": "e",
}

_LEGACY_SEED_IDS = {
    "rt-a": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a1"),
    "rt-b": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a2"),
    "rt-c": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a3"),
    "rt-d": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a4"),
    "rt-e": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a5"),
    "tp-a": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b0"),
    "tp-b": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b1"),
    "tp-c": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b2"),
    "tp-d": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b3"),
    "tp-e": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b4"),
    "re-a": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000c0"),
    "re-b": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000c1"),
    "re-c": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000c2"),
    "re-d": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000c3"),
    "re-e": UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000c4"),
}

# Legacy rows from 0003_searches
LEGACY_SEARCH_IDS = (
    UUID("aaaaaaaa-bbbb-4ccc-8ddd-000000000001"),
    UUID("aaaaaaaa-bbbb-4ccc-8ddd-000000000002"),
)

# limit_n=0 → no product cap (soft unlimited)
_DEFAULT_LIMIT = 0

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

PLATFORM_ORDER = (
    "rostender",
    "tender-pro",
    "roseltorg",
    "b2b-center",
    "rts-rosatom",
    "oilb2bcs",
    "sibur-srm",
)
PLATFORM_LABELS = {
    "rostender": "РосТендер",
    "tender-pro": "Tender.Pro",
    "roseltorg": "Росэлторг",
    "b2b-center": "B2B-Center",
    "rts-rosatom": "РТС (Росатом)",
    "oilb2bcs": "OilB2B",
    "sibur-srm": "СИБУР SRM",
}


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
            "name": "услуги НК",
            "queries": list(_PACKAGE_A_QUERIES),
            "exclude": _exclude_supply(),
        },
        {
            "key": "b",
            "name": "методы",
            "queries": list(_PACKAGE_B_QUERIES),
            "exclude": _exclude_supply(),
        },
        {
            "key": "c",
            "name": "аббревиатуры",
            "queries": list(_PACKAGE_C_QUERIES),
            "exclude": _exclude_supply(),
        },
        {
            "key": "d",
            "name": "контроли",
            "queries": list(_PACKAGE_D_QUERIES),
            "exclude": _exclude_d_full(),
        },
        {
            "key": "e",
            "name": "страховка",
            "queries": list(_PACKAGE_E_QUERIES),
            "exclude": _exclude_supply(),
        },
    ]


def group_seed_rows(*, in_queue: bool = True) -> list[dict[str, Any]]:
    """Five A–E search groups (no platform_id)."""
    rows: list[dict[str, Any]] = []
    for i, pkg in enumerate(_shared_packages()):
        rows.append(
            {
                "id": _GROUP_IDS[pkg["key"]],
                "name": pkg["name"],
                "queries": list(pkg["queries"]),
                "exclude": list(pkg["exclude"]),
                "limit_n": _DEFAULT_LIMIT,
                "in_queue": in_queue,
                "sort_order": i + 1,
            }
        )
    return rows


def legacy_seed_id_to_group_id() -> dict[UUID, UUID]:
    """Map pre-048 per-platform seed UUIDs → group UUID."""
    out: dict[UUID, UUID] = {}
    for seed_key, group_key in _LEGACY_SEED_TO_GROUP_KEY.items():
        out[_LEGACY_SEED_IDS[seed_key]] = _GROUP_IDS[group_key]
    return out


# --- Back-compat aliases for tests that still import old helpers ---

# Deprecated name kept for import stability during 048 test updates.
_SEED_IDS = _LEGACY_SEED_IDS


def seeds_for_platform(
    *,
    platform_id: str,
    name_prefix: str,
    id_prefix: str,
    sort_base: int,
    in_queue: bool,
) -> list[dict[str, Any]]:
    """Deprecated: expand groups as platform-prefixed rows (shim / old tests)."""
    rows: list[dict[str, Any]] = []
    for i, pkg in enumerate(_shared_packages()):
        seed_key = f"{id_prefix}-{pkg['key']}"
        rows.append(
            {
                "id": _LEGACY_SEED_IDS[seed_key],
                "name": f"{name_prefix} — {pkg['name']}",
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
    """Deprecated: 15 platform×package rows — prefer group_seed_rows()."""
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

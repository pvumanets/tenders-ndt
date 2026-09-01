"""RTS Rosatom market adapter (B2B/RTS stack on rosatom.rts-tender.ru)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.worker import rts_market
from app.worker.platform_ids import PLATFORM_RTS_ROSATOM, compose_tender_id

SITE = rts_market.RtsMarketSite(
    platform_id=PLATFORM_RTS_ROSATOM,
    default_base="https://www.rosatom.rts-tender.ru",
    cookies_env="RTS_ROSATOM_COOKIES_FILE",
    default_cookies_file="./cookies.rts-rosatom.txt",
    base_url_env="RTS_ROSATOM_BASE_URL",
    probe_markers=("rts-tender", "b2b-center", "rosatom"),
)

DEFAULT_BASE = SITE.default_base
RtsRosatomRow = rts_market.RtsMarketRow


def cookies_path() -> Path:
    return rts_market.cookies_path(SITE)


def cookies_present() -> bool:
    return rts_market.cookies_present(SITE)


def base_url() -> str:
    return rts_market.base_url(SITE)


def card_url(native_id: str, *, base: str | None = None) -> str:
    return rts_market.card_url(SITE, native_id, base=base)


def list_query_params(keyword: str, *, page: int = 1) -> dict[str, str]:
    return rts_market.list_query_params(keyword, page=page)


def parse_list_html(html: str, *, base: str | None = None) -> list[rts_market.RtsMarketRow]:
    return rts_market.parse_list_html(html, site=SITE, base=base)


def parse_card_html(html: str, *, title_hint: str = "", base: str | None = None) -> dict[str, Any]:
    return rts_market.parse_card_html(html, title_hint=title_hint, base=base)


def probe_rts_rosatom_session(
    path: Path | None = None,
    base_url_arg: str | None = None,
    *,
    on_retry=None,
) -> str:
    return rts_market.probe_session(SITE, path, base_url_arg, on_retry=on_retry)


def scrape_list_page(
    *,
    keyword: str,
    base: str | None = None,
    page: int = 1,
    client=None,
    on_retry=None,
) -> tuple[list[dict], Any]:
    return rts_market.scrape_list_page(
        SITE, keyword=keyword, base=base, page=page, client=client, on_retry=on_retry
    )


def scrape_queries(
    *,
    queries: list[str],
    limit: int = rts_market.POOL_LIMIT,
    base: str | None = None,
    cookies_file: Path | None = None,
    should_stop=None,
    on_progress=None,
    on_retry=None,
    client=None,
    delay_s: float = 0.15,
    exclude: list[str] | None = None,
) -> list[dict]:
    return rts_market.scrape_queries(
        SITE,
        queries=queries,
        limit=limit,
        base=base,
        cookies_file=cookies_file,
        should_stop=should_stop,
        on_progress=on_progress,
        on_retry=on_retry,
        client=client,
        delay_s=delay_s,
        exclude=exclude,
    )


def enrich_cards(
    rows: list[dict],
    card_ids: list[str],
    *,
    base: str | None = None,
    cookies_file: Path | None = None,
    delay_s: float = 0.2,
    should_stop=None,
    on_progress=None,
    on_retry=None,
    client=None,
) -> tuple[list[dict], list[dict]]:
    return rts_market.enrich_cards(
        SITE,
        rows,
        card_ids,
        base=base,
        cookies_file=cookies_file,
        delay_s=delay_s,
        should_stop=should_stop,
        on_progress=on_progress,
        on_retry=on_retry,
        client=client,
    )


def prefixed_compose(native_id: str) -> str:
    return compose_tender_id(PLATFORM_RTS_ROSATOM, native_id)

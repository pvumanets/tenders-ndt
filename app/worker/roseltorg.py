"""Roseltorg CORP list + card enrich (httpx JSON + ELK Bearer). No Playwright / docs download."""
from __future__ import annotations

import os
import time
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.deadline import deadline_date, today_msk_date
from app.worker.customer_name import clean_customer_name
from app.worker.http_retry import request_with_retry
from app.worker.list_scrape import AuthError, UA
from app.worker.platform_ids import PLATFORM_ROSELTORG, compose_tender_id

DEFAULT_LK = "https://lk.roseltorg.ru"
DEFAULT_CORP = "https://corp.roseltorg.ru"
TOKEN_PATH = "/api/app/api/auth/v1/token"
PROCEDURES_PATH = "/api/v1/procedures"
# Public SPA OAuth client (embedded in lk frontend bundle; not owner secrets).
_ELK_CLIENT_ID = "lk"
_ELK_CLIENT_SECRET = "elk"
_CORP_CLIENT_ID = "platform_223_corp"
POOL_LIMIT = 0
PAGE_SIZE = 25
MAX_PAGES = 500
# Open-only: stop after this many consecutive pages with zero open rows (API has no reliable gte).
MAX_EMPTY_OPEN_PAGES = 40
_MSK = ZoneInfo("Europe/Moscow")


def credentials_present() -> bool:
    user = (os.getenv("ROSELTORG_USER") or "").strip()
    password = (os.getenv("ROSELTORG_PASSWORD") or "").strip()
    return bool(user and password)


def _credentials() -> tuple[str, str]:
    user = (os.getenv("ROSELTORG_USER") or "").strip()
    password = (os.getenv("ROSELTORG_PASSWORD") or "").strip()
    if not user or not password:
        raise AuthError("roseltorg_missing_credentials")
    return user, password


def procedure_url(native_id: str, *, corp_base: str = DEFAULT_CORP) -> str:
    base = corp_base.rstrip("/")
    return f"{base}/#procedures/{native_id}"


def format_deadline_msk(raw: object) -> str | None:
    """Keep ISO date prefix so deadline_date() parses; strip timezone noise for display."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    return text


def map_procedure_row(item: dict[str, Any], *, corp_base: str = DEFAULT_CORP) -> dict[str, Any]:
    native = str(item.get("id") or "").strip()
    if not native:
        raise ValueError("empty_procedure_id")
    title = str(item.get("name") or "").strip() or f"Procedure {native}"
    customer = clean_customer_name(item.get("organizator"))
    deadline = format_deadline_msk(item.get("acceptanceApplicationsDateEnd"))
    price: str | None = None
    if item.get("isSumVisible") and item.get("summ") is not None:
        price = str(item.get("summ"))
    status = item.get("status") or item.get("state")
    return {
        "tender_id": native,
        "title": title,
        "url": procedure_url(native, corp_base=corp_base),
        "customer_name": customer,
        "deadline_msk": deadline,
        "price_rub": price,
        "status": str(status) if status is not None else None,
        "source_platform_id": PLATFORM_ROSELTORG,
    }


def is_open_acceptance(
    item_or_row: dict[str, Any],
    *,
    today: date | None = None,
) -> bool:
    """True when acceptanceApplicationsDateEnd calendar day >= today MSK (or undated)."""
    raw = item_or_row.get("acceptanceApplicationsDateEnd")
    if raw is None:
        raw = item_or_row.get("deadline_msk")
    due = deadline_date(format_deadline_msk(raw))
    if due is None:
        return True
    return due >= today_msk_date(today)


def obtain_corp_bearer(
    client: httpx.Client,
    *,
    lk_base: str = DEFAULT_LK,
    on_retry=None,
) -> str:
    """Password grant (lk) → session cookies → auth_token for CORP client."""
    user, password = _credentials()
    token_url = f"{lk_base.rstrip('/')}{TOKEN_PATH}"
    headers = {
        "Origin": lk_base.rstrip("/"),
        "Referer": f"{lk_base.rstrip('/')}/",
    }
    pw = request_with_retry(
        client,
        "POST",
        token_url,
        data={
            "grant_type": "password",
            "client_id": _ELK_CLIENT_ID,
            "client_secret": _ELK_CLIENT_SECRET,
            "username": user,
            "password": password,
        },
        headers=headers,
        on_retry=on_retry,
    )
    if pw.status_code in {401, 403}:
        raise AuthError("roseltorg_login_rejected")
    pw.raise_for_status()
    if "access_token" not in (pw.text or ""):
        raise AuthError("roseltorg_login_no_token")

    corp = request_with_retry(
        client,
        "POST",
        token_url,
        data={
            "grant_type": "auth_token",
            "client_id": _CORP_CLIENT_ID,
        },
        headers=headers,
        on_retry=on_retry,
    )
    if corp.status_code in {401, 403}:
        raise AuthError("roseltorg_corp_token_rejected")
    corp.raise_for_status()
    payload = corp.json()
    token = str(payload.get("access_token") or "").strip()
    if not token:
        raise AuthError("roseltorg_corp_token_empty")
    return token


def probe_roseltorg_session(
    *,
    lk_base: str = DEFAULT_LK,
    corp_base: str = DEFAULT_CORP,
    on_retry=None,
) -> str:
    """ok | missing | expired — ELK credentials + short CORP list probe."""
    if not credentials_present():
        return "missing"
    try:
        with httpx.Client(
            headers={"User-Agent": UA, "Accept": "application/json"},
            follow_redirects=True,
            timeout=60.0,
        ) as client:
            token = obtain_corp_bearer(client, lk_base=lk_base, on_retry=on_retry)
            response = request_with_retry(
                client,
                "GET",
                f"{corp_base.rstrip('/')}{PROCEDURES_PATH}",
                params={"query": "контроль", "limit": 1, "offset": 0},
                headers={"Authorization": f"Bearer {token}"},
                on_retry=on_retry,
            )
            if response.status_code in {401, 403}:
                return "expired"
            response.raise_for_status()
            if "items" not in (response.json() or {}):
                return "expired"
        return "ok"
    except AuthError:
        return "expired"
    except Exception:  # noqa: BLE001
        return "expired"


def fetch_procedures_page(
    *,
    query: str,
    token: str,
    corp_base: str = DEFAULT_CORP,
    limit: int = PAGE_SIZE,
    offset: int = 0,
    client: httpx.Client | None = None,
    on_retry=None,
    extra_params: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], int | None]:
    own = client is None
    if own:
        client = httpx.Client(
            headers={"User-Agent": UA, "Accept": "application/json"},
            follow_redirects=True,
            timeout=60.0,
        )
    assert client is not None
    try:
        params: dict[str, Any] = {"query": query, "limit": limit, "offset": offset}
        if extra_params:
            params.update(extra_params)
        response = request_with_retry(
            client,
            "GET",
            f"{corp_base.rstrip('/')}{PROCEDURES_PATH}",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            on_retry=on_retry,
        )
        if response.status_code in {401, 403}:
            raise AuthError("roseltorg_session_expired")
        response.raise_for_status()
        payload = response.json() or {}
        items = payload.get("items") or []
        if not isinstance(items, list):
            items = []
        count = payload.get("count")
        total = int(count) if count is not None else None
        return [dict(x) for x in items if isinstance(x, dict)], total
    finally:
        if own:
            client.close()


def scrape_queries(
    *,
    queries: list[str],
    limit: int = POOL_LIMIT,
    corp_base: str = DEFAULT_CORP,
    lk_base: str = DEFAULT_LK,
    should_stop=None,
    on_progress=None,
    on_retry=None,
    client: httpx.Client | None = None,
    delay_s: float = 0.15,
    exclude: list[str] | None = None,
    open_only: bool = True,
    today: date | None = None,
    bearer_token: str | None = None,
) -> list[dict]:
    """Union of query searches, open-only filter, dedupe by native id, soft cap if limit>0."""
    from app.worker.exclude_filter import filter_rows_by_exclude

    cap = None if int(limit or 0) <= 0 else int(limit)
    progress_total = cap if cap is not None else 0
    combined: list[dict] = []
    seen: set[str] = set()
    own = client is None
    if own:
        client = httpx.Client(
            headers={"User-Agent": UA, "Accept": "application/json"},
            follow_redirects=True,
            timeout=60.0,
        )
    assert client is not None
    try:
        token = bearer_token or obtain_corp_bearer(client, lk_base=lk_base, on_retry=on_retry)
        # UI «Активные»; client still filters by acceptanceApplicationsDateEnd.
        list_extra = {"visibility": "active"} if open_only else None
        for query in queries:
            if should_stop and should_stop():
                break
            if cap is not None and len(combined) >= cap:
                break
            q = str(query).strip()
            if not q:
                continue
            offset = 0
            page = 0
            empty_open_streak = 0
            while page < MAX_PAGES and (cap is None or len(combined) < cap):
                if should_stop and should_stop():
                    break
                batch, total = fetch_procedures_page(
                    query=q,
                    token=token,
                    corp_base=corp_base,
                    limit=PAGE_SIZE,
                    offset=offset,
                    client=client,
                    on_retry=on_retry,
                    extra_params=list_extra,
                )
                if not batch:
                    break
                new = 0
                open_on_page = 0
                for raw in batch:
                    if open_only and not is_open_acceptance(raw, today=today):
                        continue
                    open_on_page += 1
                    try:
                        row = map_procedure_row(raw, corp_base=corp_base)
                    except ValueError:
                        continue
                    tid = str(row.get("tender_id") or "")
                    if not tid or tid in seen:
                        continue
                    seen.add(tid)
                    combined.append(row)
                    new += 1
                    if cap is not None and len(combined) >= cap:
                        break
                if on_progress:
                    on_progress(len(combined), progress_total)
                if open_only:
                    if open_on_page == 0:
                        empty_open_streak += 1
                    else:
                        empty_open_streak = 0
                offset += PAGE_SIZE
                page += 1
                if total is not None and offset >= total:
                    break
                if len(batch) < PAGE_SIZE:
                    break
                if open_only and total is None and empty_open_streak >= MAX_EMPTY_OPEN_PAGES:
                    break
                if delay_s > 0:
                    time.sleep(delay_s)
        out = combined if cap is None else combined[:cap]
        return filter_rows_by_exclude(out, exclude)
    except AuthError:
        out = combined if cap is None else combined[:cap]
        return filter_rows_by_exclude(out, exclude)
    finally:
        if own:
            client.close()


def parse_card_payload(payload: dict[str, Any], *, title_hint: str = "") -> dict[str, Any]:
    title = str(payload.get("name") or title_hint or "").strip() or title_hint
    deadline = format_deadline_msk(payload.get("acceptanceApplicationsDateEnd"))
    customer = clean_customer_name(payload.get("organizator"))
    bits: list[str] = []
    for key in ("description", "subject", "purchaseMethod", "procedureType", "additionalInfo"):
        val = payload.get(key)
        if val:
            bits.append(str(val))
    # nested blobs sometimes carry lot names
    lots = payload.get("lots")
    if isinstance(lots, list):
        for lot in lots[:20]:
            if isinstance(lot, dict):
                name = lot.get("name") or lot.get("subject")
                if name:
                    bits.append(str(name))
    fit_extra = " ".join(bits)[:4000] or None
    status = payload.get("status") or payload.get("state")
    return {
        "title": title or None,
        "deadline_msk": deadline,
        "customer_name": customer,
        "status": str(status) if status is not None else None,
        "description": fit_extra,
        "fit_extra": fit_extra,
        "card_fetched": True,
        "doc_links": [],  # v1: docs download out of scope
    }


def enrich_cards(
    rows: list[dict],
    card_ids: list[str],
    *,
    corp_base: str = DEFAULT_CORP,
    lk_base: str = DEFAULT_LK,
    delay_s: float = 0.2,
    should_stop=None,
    on_progress=None,
    on_retry=None,
    client: httpx.Client | None = None,
    bearer_token: str | None = None,
) -> tuple[list[dict], list[dict]]:
    by_id = {str(r.get("tender_id") or ""): r for r in rows}
    errors: list[dict] = []
    own = client is None
    if own:
        client = httpx.Client(
            headers={"User-Agent": UA, "Accept": "application/json"},
            follow_redirects=True,
            timeout=60.0,
        )
    assert client is not None
    try:
        token = bearer_token or obtain_corp_bearer(client, lk_base=lk_base, on_retry=on_retry)
        total = len(card_ids)
        for i, raw_id in enumerate(card_ids, start=1):
            if should_stop and should_stop():
                break
            if on_progress:
                on_progress(i - 1, total)
            key = str(raw_id)
            row = by_id.get(key)
            if row is None:
                native = key.split(":", 1)[-1]
                for candidate, candidate_row in by_id.items():
                    if candidate == key or candidate.endswith(":" + native) or candidate == native:
                        row = candidate_row
                        key = candidate
                        break
            if row is None:
                errors.append({"tender_id": raw_id, "error": "missing_in_scored"})
                continue
            native = key.split(":", 1)[-1]
            url = f"{corp_base.rstrip('/')}{PROCEDURES_PATH}/{native}"
            try:
                response = request_with_retry(
                    client,
                    "GET",
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    on_retry=on_retry,
                )
                if response.status_code in {401, 403}:
                    raise AuthError("roseltorg_session_expired")
                if response.status_code == 404:
                    errors.append({"tender_id": key, "error": "http_404"})
                    row["card_error"] = "http_404"
                    continue
                response.raise_for_status()
                payload = response.json() or {}
                if not isinstance(payload, dict):
                    payload = {}
                # some APIs wrap under data/item
                for wrap in ("data", "item", "procedure"):
                    inner = payload.get(wrap)
                    if isinstance(inner, dict) and ("name" in inner or "id" in inner):
                        payload = inner
                        break
                parsed = parse_card_payload(payload, title_hint=str(row.get("title") or ""))
                row.update({k: v for k, v in parsed.items() if v is not None})
            except AuthError:
                raise
            except Exception as exc:  # noqa: BLE001
                row["card_error"] = f"{type(exc).__name__}: {exc}"
                errors.append({"tender_id": key, "error": row["card_error"]})
            if delay_s > 0:
                time.sleep(delay_s)
        if on_progress:
            on_progress(total, total)
        return rows, errors
    finally:
        if own:
            client.close()


def prefixed_compose(native_id: str) -> str:
    return compose_tender_id(PLATFORM_ROSELTORG, native_id)


def today_msk_calendar() -> date:
    return datetime.now(_MSK).date()

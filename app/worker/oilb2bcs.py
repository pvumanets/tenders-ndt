"""OilB2B (oilb2bcs.ru) list via Ext.NET DirectEvent GetClaims (httpx)."""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from app.worker.cookies import parse_netscape_cookies
from app.worker.http_retry import request_with_retry
from app.worker.list_scrape import AuthError, UA
from app.worker.platform_ids import PLATFORM_OILB2BCS, compose_tender_id

DEFAULT_BASE = "https://oilb2bcs.ru"
INDEX_PATH = "/indexOil.aspx"
POOL_LIMIT = 0
MAX_PAGES = 100
_PAGE_SIZE = 50
_AUTH_COOKIES = frozenset({"ASP.NET_SessionId", ".ASPXAUTH", "SERVERID"})
_REPO_ROOT = Path(__file__).resolve().parents[2]
_EXTNET_KEY = re.compile(r"(\{|,)(\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)")


@dataclass
class OilB2BRow:
    tender_id: str
    title: str
    url: str
    customer_name: str | None = None
    deadline_msk: str | None = None
    status: str | None = None


def cookies_path() -> Path:
    raw = os.getenv("OILB2BCS_COOKIES_FILE", "./cookies.oilb2bcs.txt").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path


def cookies_present() -> bool:
    path = cookies_path()
    if not path.is_file():
        return False
    try:
        return bool(_cookie_dict(path))
    except OSError:
        return False


def base_url() -> str:
    return (os.getenv("OILB2BCS_BASE_URL") or DEFAULT_BASE).rstrip("/")


def card_url(native_id: str, *, base: str | None = None) -> str:
    root = (base or base_url()).rstrip("/")
    return f"{root}{INDEX_PATH}#claim-{str(native_id).strip()}"


def _cookie_dict(path: Path | None = None) -> dict[str, str]:
    jar_path = path or cookies_path()
    if not jar_path.is_file():
        return {}
    out: dict[str, str] = {}
    try:
        for item in parse_netscape_cookies(jar_path):
            name = str(item.get("name") or "")
            if name not in _AUTH_COOKIES:
                continue
            value = str(item.get("value") or "")
            if name and value:
                out[name] = value
    except OSError:
        return {}
    return out


def _hidden_field(html: str, name: str) -> str:
    m = re.search(rf'name="{re.escape(name)}"[^>]*value="([^"]*)"', html, re.I)
    return m.group(1) if m else ""


def _parse_extnet_payload(text: str) -> Any:
    body = text.strip()
    if body.startswith("status="):
        body = body.split("\n", 1)[-1].strip()
    if not body.startswith("{"):
        start = body.find("{")
        if start < 0:
            raise ValueError("oilb2b_invalid_response")
        body = body[start:]
    fixed = _EXTNET_KEY.sub(r'\1\2"\3"\4', body)
    payload = json.loads(fixed)
    if isinstance(payload, dict) and "result" in payload:
        return payload["result"]
    return payload


def _format_deadline(raw: str | None) -> str | None:
    if not raw:
        return None
    text = str(raw).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(text[:26], fmt)
            return dt.strftime("%d.%m.%Y %H:%M")
        except ValueError:
            continue
    m = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    return m.group(1) if m else text[:32]


def _rows_from_claims(
    claims: list[dict],
    items: list[dict] | None,
    *,
    base: str,
) -> list[dict]:
    by_claim: dict[int, list[dict]] = {}
    for item in items or []:
        if not isinstance(item, dict):
            continue
        pid = item.get("planclaim")
        if pid is None:
            continue
        by_claim.setdefault(int(pid), []).append(item)

    rows: list[dict] = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        native = str(claim.get("Id") or "").strip()
        if not native.isdigit():
            continue
        line_items = by_claim.get(int(native), [])
        title = str(claim.get("CategoryText") or "").strip()
        if not title and line_items:
            title = str(line_items[0].get("name") or "").strip()
        if not title:
            title = f"Заявка {native}"
        desc_parts = [
            str(it.get("name") or "").strip()
            for it in line_items
            if str(it.get("name") or "").strip()
        ]
        row = OilB2BRow(
            tender_id=native,
            title=title[:500],
            url=card_url(native, base=base),
            customer_name=str(claim.get("CustomerText") or "").strip() or None,
            deadline_msk=_format_deadline(str(claim.get("Stop") or "")),
            status=str(claim.get("State") or "") or None,
        )
        item = asdict(row)
        if desc_parts:
            item["description"] = "\n".join(desc_parts)[:2000]
        rows.append(item)
    return rows


_POST_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "X-Ext.Net": "delta=true",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}


def _fetch_claims_page(
    client: httpx.Client,
    *,
    keyword: str,
    page: int,
    page_size: int,
    viewstate: str,
    validation: str,
    generator: str,
    base: str,
    on_retry=None,
) -> tuple[int, list[dict], list[dict]]:
    config = {
        "config": {
            "extraParams": {
                "name": keyword,
                "org": "",
                "fio": "",
                "dt1": "",
                "dt2": "",
                "category": "",
                "page": page,
                "pageSize": page_size,
                "sort": "time",
                "dir": "desc",
            }
        }
    }
    data = {
        "submitDirectEventConfig": json.dumps(config, ensure_ascii=False),
        "__EVENTTARGET": "ctl00$ResourceManager",
        "__EVENTARGUMENT": "-|public|GetClaims",
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": generator,
        "__EVENTVALIDATION": validation,
    }
    url = f"{base}{INDEX_PATH}?{urlencode({'_dc': str(int(time.time() * 1000))})}"
    response = request_with_retry(
        client, "POST", url, data=data, headers=_POST_HEADERS, on_retry=on_retry
    )
    if response.status_code in {401, 403}:
        raise AuthError("oilb2bcs_session_expired")
    response.raise_for_status()
    if response.text.lstrip().startswith("<!DOCTYPE"):
        raise AuthError("oilb2bcs_session_expired")
    result = _parse_extnet_payload(response.text)
    if not isinstance(result, list) or len(result) < 2:
        return 0, [], []
    total = int(result[0] or 0)
    claims = result[1] if isinstance(result[1], list) else []
    items = result[2] if len(result) > 2 and isinstance(result[2], list) else []
    return total, claims, items


def probe_oilb2bcs_session(
    path: Path | None = None,
    base_url_arg: str | None = None,
    *,
    on_retry=None,
) -> str:
    cookies_file = path or cookies_path()
    if not cookies_file.is_file():
        return "missing"
    cookies = _cookie_dict(cookies_file)
    if not cookies:
        return "missing"
    root = (base_url_arg or base_url()).rstrip("/")
    headers = {
        "User-Agent": UA,
        "Accept-Language": "ru-RU,ru;q=0.9",
        "Referer": f"{root}{INDEX_PATH}",
    }
    try:
        with httpx.Client(
            cookies=cookies, headers=headers, follow_redirects=True, timeout=60.0
        ) as client:
            response = request_with_retry(client, "GET", f"{root}{INDEX_PATH}", on_retry=on_retry)
            if response.status_code in {401, 403}:
                return "expired"
            final = str(response.url).lower()
            if "error.aspx" in final or "login" in final:
                return "expired"
            if ".aspxauth" not in {k.lower() for k in cookies} and "indexoil" not in final:
                return "expired"
            text = response.text.lower()
            if "directmethods" in text and "getclaims" in text:
                return "ok"
            return "expired"
    except Exception:  # noqa: BLE001
        return "expired"


def scrape_queries(
    *,
    queries: list[str],
    limit: int = POOL_LIMIT,
    base: str | None = None,
    cookies_file: Path | None = None,
    should_stop=None,
    on_progress=None,
    on_retry=None,
    client: httpx.Client | None = None,
    delay_s: float = 0.15,
    exclude: list[str] | None = None,
) -> list[dict]:
    from app.worker.exclude_filter import filter_rows_by_exclude

    root = (base or base_url()).rstrip("/")
    cap = None if int(limit or 0) <= 0 else int(limit)
    progress_total = cap if cap is not None else 0
    combined: list[dict] = []
    seen: set[str] = set()
    jar = _cookie_dict(cookies_file) if cookies_file else _cookie_dict()
    headers = {
        "User-Agent": UA,
        "Accept-Language": "ru-RU,ru;q=0.9",
        "Referer": f"{root}{INDEX_PATH}",
    }
    own = client is None
    if own:
        client = httpx.Client(
            cookies=jar or None,
            headers=headers,
            follow_redirects=True,
            timeout=60.0,
        )
    assert client is not None
    try:
        bootstrap = request_with_retry(client, "GET", f"{root}{INDEX_PATH}", on_retry=on_retry)
        bootstrap.raise_for_status()
        viewstate = _hidden_field(bootstrap.text, "__VIEWSTATE")
        validation = _hidden_field(bootstrap.text, "__EVENTVALIDATION")
        generator = _hidden_field(bootstrap.text, "__VIEWSTATEGENERATOR")
        if not viewstate:
            raise AuthError("oilb2bcs_session_expired")

        for query in queries:
            if should_stop and should_stop():
                break
            if cap is not None and len(combined) >= cap:
                break
            q = str(query).strip()
            if not q:
                continue
            page = 1
            while page <= MAX_PAGES and (cap is None or len(combined) < cap):
                if should_stop and should_stop():
                    break
                total, claims, items = _fetch_claims_page(
                    client,
                    keyword=q,
                    page=page,
                    page_size=_PAGE_SIZE,
                    viewstate=viewstate,
                    validation=validation,
                    generator=generator,
                    base=root,
                    on_retry=on_retry,
                )
                batch = _rows_from_claims(claims, items, base=root)
                if not batch:
                    break
                new = 0
                for row in batch:
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
                if new == 0:
                    break
                if page * _PAGE_SIZE >= total:
                    break
                page += 1
                if delay_s > 0:
                    time.sleep(delay_s)
        out = combined if cap is None else combined[:cap]
        return filter_rows_by_exclude(out, exclude)
    finally:
        if own:
            client.close()


def enrich_cards(
    rows: list[dict],
    card_ids: list[str],
    *,
    base: str | None = None,
    cookies_file: Path | None = None,
    delay_s: float = 0.0,
    should_stop=None,
    on_progress=None,
    on_retry=None,
    client: httpx.Client | None = None,
) -> tuple[list[dict], list[dict]]:
    """List payload already carries line items; mark cards fetched."""
    del base, cookies_file, delay_s, on_retry, client
    errors: list[dict] = []
    by_id = {str(r.get("tender_id") or ""): r for r in rows}
    total = len(card_ids)
    for i, raw_id in enumerate(card_ids, start=1):
        if should_stop and should_stop():
            break
        if on_progress:
            on_progress(i - 1, total)
        key = str(raw_id)
        row = by_id.get(key)
        if row is None:
            for candidate in by_id:
                if candidate == key or candidate.endswith(":" + key.split(":")[-1]):
                    row = by_id[candidate]
                    break
        if row is None:
            errors.append({"tender_id": raw_id, "error": "missing_in_scored"})
            continue
        row["card_fetched"] = True
    if on_progress:
        on_progress(total, total)
    return rows, errors


def prefixed_compose(native_id: str) -> str:
    return compose_tender_id(PLATFORM_OILB2BCS, native_id)

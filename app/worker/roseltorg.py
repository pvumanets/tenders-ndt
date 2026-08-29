"""Roseltorg www.roseltorg.ru list + card enrich (httpx HTML + Netscape cookies)."""
from __future__ import annotations

import os
import re
import time
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin

import httpx
from bs4 import BeautifulSoup

from app.deadline import deadline_date, today_msk_date
from app.worker.cookies import parse_netscape_cookies
from app.worker.customer_name import clean_customer_name
from app.worker.http_retry import request_with_retry
from app.worker.list_scrape import AuthError, UA
from app.worker.platform_ids import PLATFORM_ROSELTORG, compose_tender_id

DEFAULT_BASE = "https://www.roseltorg.ru"
POOL_LIMIT = 0
PAGE_SIZE = 10
MAX_PAGES = 500
# Active statuses from owner UI: Приём / подача / …
_DEFAULT_STATUSES = ("5", "0", "1")
_PROC_ID_RE = re.compile(
    r"\b((?:ATOM|COM|RH|RTST|ROSSETI|KIM(?:-INTERRAO)?|B)\d[\w-]*)\b",
    re.I,
)
_DEADLINE_ROW_RE = re.compile(
    r"Приём заявок.*?до\s+(\d{2}\.\d{2}\.\d{2,4})",
    re.I | re.S,
)
_SHORT_YEAR_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{2})\b")
_ACCEPTANCE_RE = re.compile(r"Прием заявок|Приём заявок", re.I)
_CLOSED_RE = re.compile(
    r"Заверш|Отмен|Архив|Не состоял|Работа комиссии",
    re.I,
)


def cookies_path() -> Path:
    raw = (os.getenv("ROSELTORG_COOKIES_FILE") or "./cookies.roseltorg.txt").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    return path


def cookies_present() -> bool:
    path = cookies_path()
    if not path.is_file():
        return False
    try:
        return bool(parse_netscape_cookies(path))
    except OSError:
        return False


# Back-compat alias used by older imports/tests during transition.
def credentials_present() -> bool:
    return cookies_present()


def _cookie_dict(path: Path | None = None) -> dict[str, str]:
    jar_path = path or cookies_path()
    out: dict[str, str] = {}
    for item in parse_netscape_cookies(jar_path):
        name = str(item.get("name") or "")
        value = str(item.get("value") or "")
        if name:
            out[name] = value
    if not out:
        raise AuthError("roseltorg_missing_cookies")
    return out


def base_url() -> str:
    return (os.getenv("ROSELTORG_BASE_URL") or DEFAULT_BASE).rstrip("/")


def procedure_url(native_id: str, *, lot: int = 1, base: str | None = None) -> str:
    root = (base or base_url()).rstrip("/")
    native = str(native_id).strip()
    return f"{root}/procedure/{native}/{lot}"


def normalize_deadline_msk(raw: object) -> str | None:
    """Normalize DD.MM.YY(YY) or ISO into a string deadline_date() understands."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = _SHORT_YEAR_RE.match(text)
    if m:
        yy = int(m.group(3))
        year = 2000 + yy if yy < 100 else yy
        return f"{m.group(1)}.{m.group(2)}.{year:04d}"
    return text


def extract_etp_procedure_id(*texts: object) -> str | None:
    """Pull ATOM/COM/… procedure number from free text or URL."""
    for raw in texts:
        if raw is None:
            continue
        m = _PROC_ID_RE.search(str(raw))
        if m:
            return m.group(1).upper() if m.group(1)[:4].upper() == "ATOM" else m.group(1)
    return None


def map_search_card(
    node: Any,
    *,
    base: str | None = None,
) -> dict[str, Any] | None:
    """Parse one `.js-etp-procedure-grid-item` into a list row."""
    native = str(node.get("data-feature-favorite-lots-procedure-number") or "").strip()
    if not native:
        link = node.select_one("a.js-etp-procedure-grid-procedure-link[href*='/procedure/']")
        href = (link.get("href") if link else "") or ""
        native = extract_etp_procedure_id(href) or ""
    if not native:
        return None

    title_el = node.select_one("a.search-results__link--description") or node.select_one(
        "a.js-etp-procedure-grid-procedure-link"
    )
    title = " ".join((title_el.get_text(" ", strip=True) if title_el else "").split())
    title = re.sub(r"\s+", " ", title).strip() or f"Procedure {native}"

    customer_el = node.select_one(".search-results__customer a") or node.select_one(
        ".search-results__customer .search-results__tooltip"
    )
    customer = clean_customer_name(
        customer_el.get_text(" ", strip=True) if customer_el else None
    )

    region_el = node.select_one(".search-results__region .search-results__tooltip")
    location = region_el.get_text(" ", strip=True) if region_el else None

    status_el = node.select_one(".search-results__status")
    status = " ".join(status_el.get_text(" ", strip=True).split()) if status_el else None

    price_el = node.select_one(".search-results__sum .desktop") or node.select_one(
        ".search-results__sum"
    )
    price = None
    if price_el:
        raw_price = " ".join(price_el.get_text(" ", strip=True).split())
        if re.search(r"\d", raw_price):
            price = raw_price.replace("\xa0", " ")

    href_el = node.select_one("a.js-etp-procedure-grid-procedure-link[href*='/procedure/']")
    href = (href_el.get("href") if href_el else "") or f"/procedure/{native}/1"
    url = urljoin(base_url() + "/", href)

    return {
        "tender_id": native,
        "title": title,
        "url": url,
        "customer_name": customer,
        "location": location,
        "deadline_msk": None,
        "price_rub": price,
        "status": status,
        "source_platform_id": PLATFORM_ROSELTORG,
        "etp_procedure_id": native,
    }


def is_open_acceptance(
    item_or_row: dict[str, Any],
    *,
    today: date | None = None,
) -> bool:
    """Open when deadline >= today MSK; undated falls back to acceptance status text."""
    raw = item_or_row.get("deadline_msk") or item_or_row.get("acceptanceApplicationsDateEnd")
    due = deadline_date(normalize_deadline_msk(raw))
    if due is not None:
        return due >= today_msk_date(today)
    status = str(item_or_row.get("status") or "")
    if _CLOSED_RE.search(status) and not _ACCEPTANCE_RE.search(status):
        return False
    if _ACCEPTANCE_RE.search(status):
        return True
    # Undated + unknown status: keep (enrich may close later).
    return True


def probe_roseltorg_session(
    *,
    cookies_file: Path | None = None,
    base: str | None = None,
    on_retry=None,
) -> str:
    """Return ok | missing | expired for www search session."""
    path = cookies_file or cookies_path()
    if not path.is_file():
        return "missing"
    try:
        cookies = _cookie_dict(path)
    except AuthError:
        return "missing"
    root = (base or base_url()).rstrip("/")
    try:
        with httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
            cookies=cookies,
            follow_redirects=True,
            timeout=60.0,
        ) as client:
            response = request_with_retry(
                client,
                "GET",
                f"{root}/procedures/search",
                on_retry=on_retry,
            )
            if response.status_code in {401, 403}:
                return "expired"
            text = response.text.lower()
            if "password" in text and "войти" in text and "auction-procedures" not in text:
                return "expired"
            response.raise_for_status()
            return "ok"
    except AuthError:
        return "expired"
    except Exception:  # noqa: BLE001
        return "expired"


def fetch_search_page(
    *,
    query: str,
    page: int,
    token_cookies: dict[str, str],
    base: str | None = None,
    client: httpx.Client | None = None,
    on_retry=None,
    statuses: tuple[str, ...] = _DEFAULT_STATUSES,
) -> list[dict[str, Any]]:
    root = (base or base_url()).rstrip("/")
    params: list[tuple[str, str]] = [
        ("sale", "1"),
        ("query_field", query),
        ("currency", "all"),
        ("page", str(page)),
    ]
    for st in statuses:
        params.append(("status[]", st))
    url = f"{root}/procedures/search?{urlencode(params)}"
    own = client is None
    if own:
        client = httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
            cookies=token_cookies,
            follow_redirects=True,
            timeout=60.0,
        )
    assert client is not None
    try:
        response = request_with_retry(client, "GET", url, on_retry=on_retry)
        if response.status_code in {401, 403}:
            raise AuthError("roseltorg_session_expired")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rows: list[dict[str, Any]] = []
        for node in soup.select(".js-etp-procedure-grid-item"):
            mapped = map_search_card(node, base=root)
            if mapped:
                rows.append(mapped)
        return rows
    finally:
        if own:
            client.close()


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
    open_only: bool = True,
    today: date | None = None,
) -> list[dict]:
    """Union of www searches, open-only filter, dedupe by native id, soft cap if limit>0."""
    from app.worker.exclude_filter import filter_rows_by_exclude

    cap = None if int(limit or 0) <= 0 else int(limit)
    progress_total = cap if cap is not None else 0
    combined: list[dict] = []
    seen: set[str] = set()
    cookies = _cookie_dict(cookies_file)
    root = (base or base_url()).rstrip("/")
    own = client is None
    if own:
        client = httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
            cookies=cookies,
            follow_redirects=True,
            timeout=60.0,
        )
    assert client is not None
    try:
        for query in queries:
            if should_stop and should_stop():
                break
            q = str(query or "").strip()
            if not q:
                continue
            for page in range(0, MAX_PAGES):
                if should_stop and should_stop():
                    break
                if cap is not None and len(combined) >= cap:
                    break
                batch = fetch_search_page(
                    query=q,
                    page=page,
                    token_cookies=cookies,
                    base=root,
                    client=client,
                    on_retry=on_retry,
                )
                if not batch:
                    break
                added = 0
                for row in batch:
                    native = str(row.get("tender_id") or "")
                    if not native or native in seen:
                        continue
                    if open_only and not is_open_acceptance(row, today=today):
                        continue
                    seen.add(native)
                    combined.append(row)
                    added += 1
                    if on_progress:
                        on_progress(len(combined), progress_total)
                    if cap is not None and len(combined) >= cap:
                        break
                if len(batch) < PAGE_SIZE:
                    break
                # empty-open page still advances; stop if nothing new kept and short page
                if added == 0 and page > 0:
                    # keep scanning a bit — active filter already applied by status[]
                    pass
                time.sleep(delay_s)
        out = combined if cap is None else combined[:cap]
        return filter_rows_by_exclude(out, exclude)
    finally:
        if own:
            client.close()


def parse_card_html(html: str, *, page_url: str) -> dict[str, Any]:
    """Fields + doc_links from www `/procedure/{id}/1` HTML."""
    soup = BeautifulSoup(html, "html.parser")
    title = ""
    h1 = soup.select_one("h1")
    if h1:
        title = " ".join(h1.get_text(" ", strip=True).split())
    lot_title = soup.select_one(".lot-composition__lot-title")
    if lot_title:
        title = " ".join(lot_title.get_text(" ", strip=True).split()) or title

    customer = None
    for row in soup.select(".lot-common-info__row"):
        label = " ".join(row.select_one(".lot-common-info__text").get_text(" ", strip=True).split()) if row.select_one(".lot-common-info__text") else ""
        value_el = row.select_one(".lot-common-info__value")
        value = " ".join(value_el.get_text(" ", strip=True).split()) if value_el else ""
        if "организатор" in label.lower() or "заказчик" in label.lower():
            customer = clean_customer_name(value)
            break
    if not customer:
        org = soup.select_one("a[href*='/companies/resolve/']")
        if org:
            customer = clean_customer_name(org.get_text(" ", strip=True))

    deadline = None
    text_blob = soup.get_text("\n", strip=True)
    m = _DEADLINE_ROW_RE.search(text_blob)
    if m:
        deadline = normalize_deadline_msk(m.group(1))
    else:
        for row in soup.select(".lot-common-info__row"):
            label = row.get_text(" ", strip=True)
            if "Приём заявок" in label or "Прием заявок" in label:
                dm = re.search(r"(\d{2}\.\d{2}\.\d{2,4})", label)
                if dm:
                    deadline = normalize_deadline_msk(dm.group(1))
                    break

    status_el = soup.select_one(".lot-composition-status") or soup.select_one(
        ".search-results__status"
    )
    status = " ".join(status_el.get_text(" ", strip=True).split()) if status_el else None

    price = None
    price_el = soup.select_one(".lot-composition-price__amount")
    if price_el:
        price = " ".join(price_el.get_text(" ", strip=True).split())

    location = None
    region = soup.select_one(".search-results__region .search-results__tooltip")
    if region:
        location = region.get_text(" ", strip=True)

    doc_links: list[dict[str, str]] = []
    seen: set[str] = set()
    for a in soup.select(".lot-docs__list a[href], .lot-docs a[href]"):
        href = str(a.get("href") or "").strip()
        if not href or href.startswith("#"):
            continue
        absolute = urljoin(page_url, href)
        if absolute in seen:
            continue
        if "/file/get/" not in absolute and not re.search(
            r"\.(pdf|docx?|xlsx?|zip|rar|7z)(?:\?|$)", absolute, re.I
        ):
            # section file/get is the main pattern; also allow direct files
            if "file" not in absolute.lower() and "download" not in absolute.lower():
                continue
        seen.add(absolute)
        name = " ".join(a.get_text(" ", strip=True).split()) or "document"
        doc_links.append({"name": name, "url": absolute})

    # description / fit_extra from title + tags
    tags = [
        " ".join(chip.get_text(" ", strip=True).split())
        for chip in soup.select(".procedure-tags .chip, .search-results__tags .chip")
    ]
    fit_parts = [p for p in [title, " · ".join(tags)] if p]
    fit_extra = "\n".join(fit_parts)[:800] if fit_parts else None

    return {
        "title": title or None,
        "customer_name": customer,
        "deadline_msk": deadline,
        "status": status,
        "price_rub": price,
        "location": location,
        "doc_links": doc_links,
        "fit_extra": fit_extra,
        "card_fetched": True,
        "etp_procedure_id": extract_etp_procedure_id(page_url, title),
    }


def parse_card_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Test helper: map a dict-shaped card into enrich fields (www-era)."""
    native = str(payload.get("id") or payload.get("tender_id") or "").strip()
    title = str(payload.get("name") or payload.get("title") or "").strip()
    desc = str(payload.get("description") or "").strip()
    lots = payload.get("lots") or []
    lot_bits = []
    if isinstance(lots, list):
        for lot in lots:
            if isinstance(lot, dict) and lot.get("name"):
                lot_bits.append(str(lot["name"]))
    fit = "\n".join(x for x in [desc, " · ".join(lot_bits)] if x)[:800] or None
    return {
        "title": title or None,
        "customer_name": clean_customer_name(payload.get("organizator") or payload.get("customer_name")),
        "deadline_msk": normalize_deadline_msk(
            payload.get("acceptanceApplicationsDateEnd") or payload.get("deadline_msk")
        ),
        "doc_links": list(payload.get("doc_links") or []),
        "fit_extra": fit,
        "card_fetched": True,
        "etp_procedure_id": extract_etp_procedure_id(native, title),
    }


def enrich_cards(
    rows: list[dict],
    card_ids: list[str],
    *,
    cookies_file: Path | None = None,
    base: str | None = None,
    delay_s: float = 0.2,
    should_stop=None,
    on_progress=None,
    on_retry=None,
) -> tuple[list[dict], list[dict]]:
    """Fetch www procedure HTML for L1–L3 ids; merge fields + doc_links."""
    id_set = set(card_ids)
    by_id = {str(r.get("tender_id")): r for r in rows}
    errors: list[dict] = []
    cookies = _cookie_dict(cookies_file)
    root = (base or base_url()).rstrip("/")

    with httpx.Client(
        headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
        cookies=cookies,
        follow_redirects=True,
        timeout=60.0,
    ) as client:
        for i, tid in enumerate(card_ids, start=1):
            if should_stop and should_stop():
                break
            row = by_id.get(str(tid))
            if not row:
                errors.append({"tender_id": tid, "error": "missing_in_scored"})
                continue
            native = str(tid).split(":", 1)[-1]
            url = str(row.get("url") or procedure_url(native, base=root))
            if not url.endswith("/1") and "/procedure/" in url and url.rstrip("/").count("/") <= 4:
                # prefer lot page which carries docs + stages
                if re.search(r"/procedure/[^/]+$", url.rstrip("/")):
                    url = url.rstrip("/") + "/1"
            try:
                response = request_with_retry(client, "GET", url, on_retry=on_retry)
                if response.status_code in {401, 403}:
                    raise AuthError("roseltorg_session_expired")
                response.raise_for_status()
                parsed = parse_card_html(response.text, page_url=str(response.url))
                for key, value in parsed.items():
                    if key == "doc_links":
                        if value:
                            row["doc_links"] = value
                        continue
                    if value in (None, ""):
                        continue
                    if key == "title" and row.get("title"):
                        continue
                    row[key] = value
                row["card_fetched"] = True
                row.pop("card_error", None)
                if not row.get("etp_procedure_id"):
                    row["etp_procedure_id"] = native
            except AuthError:
                raise
            except Exception as exc:  # noqa: BLE001
                row["card_error"] = f"{type(exc).__name__}: {exc}"
                errors.append({"tender_id": tid, "error": row["card_error"]})
            if on_progress:
                on_progress(i, len(card_ids))
            time.sleep(delay_s)

    for row in rows:
        tid = str(row.get("tender_id") or "")
        if tid in id_set or row.get("tier") in ("L1", "L2", "L3"):
            if not row.get("card_fetched") and not row.get("card_error"):
                row["card_error"] = "not_attempted"
    return rows, errors


def prefixed_compose(native_id: str) -> str:
    return compose_tender_id(PLATFORM_ROSELTORG, native_id)

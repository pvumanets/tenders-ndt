"""P1: scrape first N tender rows from rostender.info (HTTP session).

Playwright against rostender returns WAF 403 from this environment; the
canonical UI fields are taken from the same HTML pages via httpx + cookies.

Pool = open tenders only: rostender `states[]=10` (Приём заявок) + deadline
from today MSK (`dte_from`). Closed / cancelled / past deadlines are out.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup

from app.worker.cookies import parse_netscape_cookies
from app.worker.customer_name import clean_customer_name
from app.worker.http_retry import request_with_retry

DEFAULT_BASE = "https://rostender.info"
SEARCH_QUERY = "неразрушающий"
POOL_LIMIT = 0  # 0 = no product cap (P11); soft stop only when caller passes limit > 0
MAX_PAGES = 500
MAX_FILTERED_EMPTY_PAGES = 3  # P14: filtered-empty pages before stop
MSK = ZoneInfo("Europe/Moscow")
OPEN_STATE = "10"  # Приём заявок
SORT_NEWEST = "0"
CLOSED_STATUS_RE = re.compile(r"Заверш[её]н|Отмен[её]н", re.I)
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


class AuthError(RuntimeError):
    """Session missing / login page."""


@dataclass
class TenderRow:
    tender_id: str
    title: str
    url: str
    price_rub: str | None
    location: str | None
    customer_name: str | None
    deadline_msk: str | None = None
    status: str | None = None


def _cookie_dict(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for c in parse_netscape_cookies(path):
        out[c["name"]] = c["value"]
    return out


def _extract_id(url: str) -> str:
    m = re.search(r"/(\d+)-tender-", url)
    if m:
        return m.group(1)
    m = re.search(r"/(\d+)(?:/|$|\?)", url)
    return m.group(1) if m else url.rstrip("/").split("/")[-1]


def _assert_authorized(html: str, url: str) -> None:
    low = html.lower()
    if "403 forbidden" in low and "administrative rules" in low:
        raise AuthError(f"WAF/403 at {url}")
    if re.search(r'name=["\']password["\']', low) and "войти" in low and "article class=\"tender-row\"" not in low:
        if len(html) < 80_000:
            raise AuthError(f"Login form detected at {url} — refresh cookies")


def _client(cookies_path: Path, base_url: str) -> httpx.Client:
    return httpx.Client(
        base_url=base_url.rstrip("/"),
        headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"},
        cookies=_cookie_dict(cookies_path),
        follow_redirects=True,
        timeout=60.0,
    )


def today_msk() -> datetime:
    return datetime.now(MSK)


def today_msk_dmy() -> str:
    return today_msk().strftime("%d.%m.%Y")


def parse_list_deadline(art) -> datetime | None:
    el = art.select_one(".dtend")
    raw = (el.get_text(" ", strip=True) if el else "") or ""
    raw = raw.strip()
    if not raw:
        cd = art.select_one(".tender__countdown-text")
        raw = (cd.get_text(" ", strip=True) if cd else "") or ""
        m = re.search(r"(\d{2}\.\d{2}\.\d{4})", raw)
        if m:
            try:
                return datetime.strptime(m.group(1), "%d.%m.%Y").replace(tzinfo=MSK)
            except ValueError:
                return None
        return None
    for fmt, n in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d", 10)):
        try:
            return datetime.strptime(raw[:n], fmt).replace(tzinfo=MSK)
        except ValueError:
            continue
    return None


def deadline_display(art, parsed: datetime | None) -> str | None:
    cd = art.select_one(".tender__countdown-text")
    if cd:
        m = re.search(r"(\d{2}\.\d{2}\.\d{4}(?:\s+\d{2}:\d{2})?)", cd.get_text(" ", strip=True))
        if m:
            return m.group(1)
    if parsed is None:
        return None
    if parsed.hour or parsed.minute:
        return parsed.strftime("%d.%m.%Y %H:%M")
    return parsed.strftime("%d.%m.%Y")


def is_open_upcoming(art, *, now: datetime | None = None) -> bool:
    """Keep Приём заявок with deadline ≥ today MSK; drop closed/past."""
    blob = art.get_text(" ", strip=True)
    if CLOSED_STATUS_RE.search(blob):
        return False
    parsed = parse_list_deadline(art)
    if parsed is None:
        return True
    day = (now or today_msk()).date()
    return parsed.date() >= day


def _start_search(client: httpx.Client, query: str, *, on_retry=None) -> str:
    """POST advanced search: open lots only, deadline from today, newest first."""
    r = request_with_retry(client, "GET", "/extsearch/advanced", on_retry=on_retry)
    _assert_authorized(r.text, str(r.url))
    soup = BeautifulSoup(r.text, "lxml")
    form = soup.select_one("#tenders-search-form")
    if not form:
        raise RuntimeError("Advanced search form #tenders-search-form not found — layout changed?")
    csrf_el = form.find("input", {"name": "_csrf-frontend"})
    csrf = (csrf_el.get("value") if csrf_el else "") or ""
    if not csrf:
        raise RuntimeError("Search CSRF token missing — layout changed?")
    data = {
        "_csrf-frontend": csrf,
        "path": "/extsearch/advanced",
        "mode": "advanced",
        "keywords": query,
        "states[]": OPEN_STATE,
        "dte_from": today_msk_dmy(),
        "sort": SORT_NEWEST,
        "sort_alias": "new-first",
        "open_data": "1",
    }
    r2 = request_with_retry(
        client,
        "POST",
        "/search/tenders",
        data=data,
        on_retry=on_retry,
    )
    _assert_authorized(r2.text, str(r2.url))
    return str(r2.url)


def _parse_customer(art) -> str | None:
    col = art.select_one(".customer-branches-column")
    if not col:
        return None
    text = col.get_text(" ", strip=True)
    m = re.search(r"Заказчик\s+(.+)$", text)
    raw = m.group(1).strip()[:300] if m else (text[:300] if text else None)
    return clean_customer_name(raw)


def _parse_rows_meta(
    html: str, base_url: str, *, now: datetime | None = None
) -> tuple[list[TenderRow], int]:
    """Return (open/upcoming rows, raw article.tender-row count in HTML)."""
    soup = BeautifulSoup(html, "lxml")
    articles = soup.select("article.tender-row")
    raw_count = len(articles)
    rows: list[TenderRow] = []
    seen: set[str] = set()
    for art in articles:
        a = art.select_one('a[href*="-tender-"]')
        if not a:
            continue
        href = a.get("href") or ""
        url = urljoin(base_url, href)
        tid = _extract_id(url)
        if tid in seen:
            continue
        seen.add(tid)
        title = a.get_text(" ", strip=True)
        if not title:
            desc = art.select_one(".description, .box-opisTender__text")
            title = desc.get_text(" ", strip=True) if desc else tid
        price_el = art.select_one(".starting-price__price, .starting-price--price")
        price = price_el.get_text(" ", strip=True) if price_el else None
        loc_el = art.select_one(".location")
        location = None
        if loc_el:
            location = loc_el.get_text(" ", strip=True).rstrip(",").strip()
        elif art.select_one(".delivery-address-column"):
            location = art.select_one(".delivery-address-column").get_text(" ", strip=True)
            location = re.split(r"Закупки в регионе", location)[0].strip()
        customer = _parse_customer(art)
        if not is_open_upcoming(art, now=now):
            continue
        parsed_deadline = parse_list_deadline(art)
        status = None
        blob = art.get_text(" ", strip=True)
        if re.search(r"При[её]м заявок", blob):
            status = "Приём заявок"
        rows.append(
            TenderRow(
                tender_id=tid,
                title=title,
                url=url,
                price_rub=price,
                location=location,
                customer_name=customer,
                deadline_msk=deadline_display(art, parsed_deadline),
                status=status,
            )
        )
    return rows, raw_count


def _parse_rows(html: str, base_url: str, *, now: datetime | None = None) -> list[TenderRow]:
    rows, _ = _parse_rows_meta(html, base_url, now=now)
    return rows


def probe_rostender_cookies(
    cookies_path: Path,
    base_url: str = DEFAULT_BASE,
    *,
    on_retry=None,
) -> str:
    """ok | missing | expired — live session probe (P14)."""
    if not cookies_path.is_file():
        return "missing"
    if not _cookie_dict(cookies_path):
        return "missing"
    try:
        with _client(cookies_path, base_url) as client:
            r = request_with_retry(
                client,
                "GET",
                "/extsearch/advanced",
                on_retry=on_retry,
            )
            _assert_authorized(r.text, str(r.url))
        return "ok"
    except AuthError:
        return "expired"
    except Exception:  # noqa: BLE001
        return "expired"


def scrape_list(
    *,
    cookies_path: Path,
    base_url: str = DEFAULT_BASE,
    query: str = SEARCH_QUERY,
    limit: int = POOL_LIMIT,
    headless: bool = True,  # kept for CLI compat; unused (HTTP transport)
    should_stop=None,
    on_progress=None,
    on_retry=None,
) -> list[dict]:
    del headless  # noqa: ARG001 — CLI flag retained
    if not cookies_path.is_file():
        raise FileNotFoundError(f"Cookies file not found: {cookies_path}")
    if not _cookie_dict(cookies_path):
        raise AuthError(f"No cookies parsed from {cookies_path}")

    cap = None if int(limit or 0) <= 0 else int(limit)
    progress_total = cap if cap is not None else 0
    results: list[TenderRow] = []
    seen: set[str] = set()

    with _client(cookies_path, base_url) as client:
        results_url = _start_search(client, query, on_retry=on_retry)
        page_num = 1
        filtered_empty_streak = 0
        while page_num <= MAX_PAGES and (cap is None or len(results) < cap):
            if should_stop and should_stop():
                break
            if page_num == 1:
                r = request_with_retry(client, "GET", results_url, on_retry=on_retry)
            else:
                sep = "&" if "?" in results_url else "?"
                base_q = re.sub(r"([&?])page=\d+", r"\1", results_url).rstrip("&?")
                r = request_with_retry(
                    client,
                    "GET",
                    f"{base_q}{sep}page={page_num}",
                    on_retry=on_retry,
                )
            _assert_authorized(r.text, str(r.url))
            batch, raw_count = _parse_rows_meta(r.text, base_url)
            if raw_count == 0:
                break
            if not batch:
                filtered_empty_streak += 1
                if filtered_empty_streak >= MAX_FILTERED_EMPTY_PAGES:
                    break
                page_num += 1
                continue
            filtered_empty_streak = 0
            new = 0
            for row in batch:
                if row.tender_id in seen:
                    continue
                seen.add(row.tender_id)
                results.append(row)
                new += 1
                if cap is not None and len(results) >= cap:
                    break
            if on_progress:
                on_progress(len(results), progress_total)
            if new == 0:
                page_num += 1
                continue
            page_num += 1

    if cap is None:
        return [asdict(r) for r in results]
    return [asdict(r) for r in results[:cap]]


def scrape_queries(
    *,
    cookies_path: Path,
    queries: list[str],
    limit: int = POOL_LIMIT,
    base_url: str = DEFAULT_BASE,
    should_stop=None,
    on_progress=None,
    on_retry=None,
    exclude: list[str] | None = None,
) -> list[dict]:
    """Union of keyword searches, deduped by tender_id; soft-capped only if limit > 0."""
    from app.worker.exclude_filter import filter_rows_by_exclude

    cap = None if int(limit or 0) <= 0 else int(limit)
    progress_total = cap if cap is not None else 0
    combined: list[dict] = []
    seen: set[str] = set()
    for query in queries:
        if should_stop and should_stop():
            break
        if cap is not None and len(combined) >= cap:
            break
        remaining = 0 if cap is None else max(0, cap - len(combined))
        batch = scrape_list(
            cookies_path=cookies_path,
            base_url=base_url,
            query=query,
            limit=remaining,
            should_stop=should_stop,
            on_retry=on_retry,
            on_progress=lambda n, _lim, offset=len(combined): on_progress(
                offset + n, progress_total
            )
            if on_progress
            else None,
        )
        for row in batch:
            tid = str(row.get("tender_id") or "")
            if not tid or tid in seen:
                continue
            seen.add(tid)
            combined.append(row)
            if cap is not None and len(combined) >= cap:
                break
        if on_progress:
            on_progress(len(combined), progress_total)
    if cap is None:
        out = combined
    else:
        out = combined[:cap]
    return filter_rows_by_exclude(out, exclude)


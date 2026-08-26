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

DEFAULT_BASE = "https://rostender.info"
SEARCH_QUERY = "неразрушающий"
POOL_LIMIT = 1000
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


def _start_search(client: httpx.Client, query: str) -> str:
    """POST advanced search: open lots only, deadline from today, newest first."""
    r = client.get("/extsearch/advanced")
    r.raise_for_status()
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
    r2 = client.post("/search/tenders", data=data)
    r2.raise_for_status()
    _assert_authorized(r2.text, str(r2.url))
    return str(r2.url)


def _parse_customer(art) -> str | None:
    col = art.select_one(".customer-branches-column")
    if not col:
        return None
    text = col.get_text(" ", strip=True)
    m = re.search(r"Заказчик\s+(.+)$", text)
    if m:
        return m.group(1).strip()[:300]
    # fallback: last long chunk
    return text[:300] if text else None


def _parse_rows(html: str, base_url: str, *, now: datetime | None = None) -> list[TenderRow]:
    soup = BeautifulSoup(html, "lxml")
    rows: list[TenderRow] = []
    seen: set[str] = set()
    for art in soup.select("article.tender-row"):
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
    return rows


def scrape_list(
    *,
    cookies_path: Path,
    base_url: str = DEFAULT_BASE,
    query: str = SEARCH_QUERY,
    limit: int = POOL_LIMIT,
    headless: bool = True,  # kept for CLI compat; unused (HTTP transport)
    should_stop=None,
    on_progress=None,
) -> list[dict]:
    del headless  # noqa: ARG001 — CLI flag retained
    if not cookies_path.is_file():
        raise FileNotFoundError(f"Cookies file not found: {cookies_path}")
    if not _cookie_dict(cookies_path):
        raise AuthError(f"No cookies parsed from {cookies_path}")

    results: list[TenderRow] = []
    seen: set[str] = set()

    with _client(cookies_path, base_url) as client:
        results_url = _start_search(client, query)
        page_num = 1
        while len(results) < limit and page_num <= 200:
            if should_stop and should_stop():
                break
            if page_num == 1:
                r = client.get(results_url)
            else:
                sep = "&" if "?" in results_url else "?"
                base_q = re.sub(r"([&?])page=\d+", r"\1", results_url).rstrip("&?")
                r = client.get(f"{base_q}{sep}page={page_num}")
            r.raise_for_status()
            _assert_authorized(r.text, str(r.url))
            batch = _parse_rows(r.text, base_url)
            if not batch:
                break
            new = 0
            for row in batch:
                if row.tender_id in seen:
                    continue
                seen.add(row.tender_id)
                results.append(row)
                new += 1
                if len(results) >= limit:
                    break
            if on_progress:
                on_progress(len(results), limit)
            if new == 0:
                break
            page_num += 1

    return [asdict(r) for r in results[:limit]]


def scrape_queries(
    *,
    cookies_path: Path,
    queries: list[str],
    limit: int = POOL_LIMIT,
    base_url: str = DEFAULT_BASE,
    should_stop=None,
    on_progress=None,
) -> list[dict]:
    """Union of keyword searches, deduped by tender_id, capped at limit."""
    combined: list[dict] = []
    seen: set[str] = set()
    for query in queries:
        if should_stop and should_stop():
            break
        if len(combined) >= limit:
            break
        remaining = limit - len(combined)
        batch = scrape_list(
            cookies_path=cookies_path,
            base_url=base_url,
            query=query,
            limit=remaining,
            should_stop=should_stop,
            on_progress=lambda n, _lim, offset=len(combined): on_progress(
                min(offset + n, limit), limit
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
            if len(combined) >= limit:
                break
        if on_progress:
            on_progress(len(combined), limit)
    return combined[:limit]


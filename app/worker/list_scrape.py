"""P1: scrape first N tender rows from rostender.info (HTTP session).

Playwright against rostender returns WAF 403 from this environment; the
canonical UI fields are taken from the same HTML pages via httpx + cookies.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.worker.cookies import parse_netscape_cookies

DEFAULT_BASE = "https://rostender.info"
SEARCH_QUERY = "неразрушающий"
POOL_LIMIT = 1000
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


def _start_search(client: httpx.Client, query: str) -> str:
    """POST /search/tenders → returns results URL with query hash."""
    r = client.get("/extsearch")
    r.raise_for_status()
    _assert_authorized(r.text, str(r.url))
    soup = BeautifulSoup(r.text, "lxml")
    form = soup.find("form", action="/search/tenders")
    if not form:
        raise RuntimeError("Search form /search/tenders not found — layout changed?")
    data: dict[str, str] = {}
    for inp in form.find_all("input"):
        name = inp.get("name")
        if not name:
            continue
        if inp.get("type") == "checkbox" and not inp.has_attr("checked"):
            continue
        data[name] = inp.get("value") or ""
    data["keywords"] = query
    data["mode"] = "simple"
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


def _parse_rows(html: str, base_url: str) -> list[TenderRow]:
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
        rows.append(
            TenderRow(
                tender_id=tid,
                title=title,
                url=url,
                price_rub=price,
                location=location,
                customer_name=customer,
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
        # Ensure we have query hash form for pagination
        # pages: results_url&page=N or ?page=N
        page_num = 1
        while len(results) < limit and page_num <= 200:
            if page_num == 1:
                r = client.get(results_url)
            else:
                sep = "&" if "?" in results_url else "?"
                # strip existing page=
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
            if new == 0:
                break
            page_num += 1

    return [asdict(r) for r in results[:limit]]

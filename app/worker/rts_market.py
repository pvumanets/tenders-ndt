"""RTS / B2B-Center market list + view.html cards (httpx + BeautifulSoup)."""
from __future__ import annotations

import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin

import httpx
from bs4 import BeautifulSoup

from app.worker.cookies import parse_netscape_cookies
from app.worker.http_relay import relay_configured, relay_fetch
from app.worker.http_retry import request_with_retry
from app.worker.list_scrape import AuthError, UA

LIST_PATH = "/market/"
VIEW_PATH = "/market/view.html"
POOL_LIMIT = 0
MAX_PAGES = 100
_ID_VIEW = re.compile(r"/market/view\.html\?id=(\d+)", re.I)
_ID_TENDER = re.compile(r"/tender-(\d+)/", re.I)
_DEADLINE = re.compile(
    r"(?:дата\s+окончания|при[её]м\s+заявок|при[её]м\s+предложений|"
    r"окончани[ея]\s+(?:подачи|приема\s+заявок)|до)"
    r"[^\d]{0,60}(\d{2}\.\d{2}\.\d{4}(?:\s+\d{1,2}:\d{2})?)",
    re.I,
)
_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RtsMarketSite:
    platform_id: str
    default_base: str
    cookies_env: str
    default_cookies_file: str
    base_url_env: str
    probe_markers: tuple[str, ...]


@dataclass
class RtsMarketRow:
    tender_id: str
    title: str
    url: str
    price_rub: str | None = None
    location: str | None = None
    customer_name: str | None = None
    deadline_msk: str | None = None
    status: str | None = None


def cookies_path(site: RtsMarketSite) -> Path:
    raw = os.getenv(site.cookies_env, site.default_cookies_file).strip()
    path = Path(raw)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path


def cookies_present(site: RtsMarketSite) -> bool:
    path = cookies_path(site)
    if not path.is_file():
        return False
    try:
        return bool(parse_netscape_cookies(path))
    except OSError:
        return False


def base_url(site: RtsMarketSite) -> str:
    return (os.getenv(site.base_url_env) or site.default_base).rstrip("/")


def card_url(site: RtsMarketSite, native_id: str, *, base: str | None = None) -> str:
    root = (base or base_url(site)).rstrip("/")
    return f"{root}{VIEW_PATH}?id={str(native_id).strip()}"


def list_query_params(keyword: str, *, page: int = 1) -> dict[str, str]:
    params = {
        "f_keyword": keyword,
        "searching": "1",
        "trade": "buy",
    }
    if page > 1:
        params["page"] = str(page)
    return params


def _cookie_dict(site: RtsMarketSite, path: Path | None = None) -> dict[str, str]:
    jar_path = path or cookies_path(site)
    if not jar_path.is_file():
        return {}
    out: dict[str, str] = {}
    try:
        for item in parse_netscape_cookies(jar_path):
            name = str(item.get("name") or "")
            value = str(item.get("value") or "")
            if name:
                out[name] = value
    except OSError:
        return {}
    return out


def _market_request(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    cookies: dict[str, str] | None = None,
    on_retry=None,
    **kwargs: Any,
) -> httpx.Response:
    """Direct httpx or north-hub relay when SCOUT_HTTP_RELAY_* is set."""
    if relay_configured():
        headers = dict(client.headers)
        extra = kwargs.pop("headers", None)
        if extra:
            headers.update(extra)
        jar = cookies if cookies is not None else dict(client.cookies)
        content = kwargs.get("content")
        body = content if isinstance(content, bytes) else None
        response = relay_fetch(
            method,
            url,
            headers=headers,
            cookies=jar,
            content=body,
        )
        final_url = response.extensions.get("final_url")
        if final_url:
            response = httpx.Response(
                status_code=response.status_code,
                headers=response.headers,
                content=response.content,
                request=httpx.Request(method, str(final_url)),
            )
        return response
    return request_with_retry(client, method, url, on_retry=on_retry, **kwargs)


def _is_captcha_response(response: httpx.Response) -> bool:
    final = str(response.url).lower()
    if "/captcha" in final:
        return True
    text = response.text.lower()
    if "search-results" in text:
        return False
    if "smartcaptcha" in text or "captcha-container" in text:
        return True
    return False


def _native_id_from_href(href: str) -> str | None:
    m = _ID_VIEW.search(href)
    if m:
        return m.group(1)
    m = _ID_TENDER.search(href)
    if m:
        return m.group(1)
    return None


def parse_list_html(html: str, *, site: RtsMarketSite, base: str | None = None) -> list[RtsMarketRow]:
    root = (base or base_url(site)).rstrip("/")
    soup = BeautifulSoup(html, "lxml")
    rows: list[RtsMarketRow] = []
    seen: set[str] = set()

    links = soup.select("table.search-results a.search-results-title")
    if not links:
        links = soup.select('a[href*="view.html?id="], a[href*="/tender-"]')

    for link in links:
        href = str(link.get("href") or "")
        native = _native_id_from_href(href)
        if not native or native in seen:
            continue
        seen.add(native)
        title = " ".join(link.get_text(" ", strip=True).split())
        if len(title) < 3:
            continue
        tr = link.find_parent("tr")
        blob = tr.get_text(" ", strip=True) if tr is not None else title
        deadline = None
        dm = _DEADLINE.search(blob)
        if dm:
            deadline = dm.group(1).strip()
        customer = None
        if tr is not None:
            firm = tr.select_one('a[href*="/firms/"]')
            if firm is not None:
                customer = " ".join(firm.get_text(" ", strip=True).split()) or None
        rows.append(
            RtsMarketRow(
                tender_id=native,
                title=title,
                url=card_url(site, native, base=root),
                customer_name=customer,
                deadline_msk=deadline,
            )
        )
    return rows


def parse_card_html(html: str, *, title_hint: str = "", base: str | None = None) -> dict[str, Any]:
    root = (base or "").rstrip("/")
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n", strip=True)
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    title = title_hint
    h1 = soup.find(["h1", "h2"])
    if h1:
        title = h1.get_text(" ", strip=True) or title
    if soup.title and (not title or "B2B-Center" in (title or "")):
        page_title = soup.title.get_text(strip=True)
        if page_title and "B2B-Center" not in page_title.replace("—", "-"):
            title = page_title
        elif page_title:
            parts = re.split(r"\s+[—–-]\s+", page_title)
            if parts and parts[0].strip():
                title = parts[0].strip()

    deadline = None
    dm = _DEADLINE.search(text)
    if dm:
        deadline = dm.group(1).strip()

    customer = None
    for i, ln in enumerate(lines[:80]):
        if re.search(r"^(Организатор|Заказчик)\s*:?\s*$", ln, re.I) and i + 1 < len(lines):
            customer = lines[i + 1]
            break
        m = re.match(r"^(Организатор|Заказчик)\s*:\s*(.+)$", ln, re.I)
        if m:
            customer = m.group(2).strip()
            break

    status = None
    for ln in lines[:80]:
        if re.search(r"при[её]м|открыт|завершен|закрыт|продаж", ln, re.I) and len(ln) < 120:
            status = ln
            break

    doc_links: list[dict[str, str]] = []
    for a in soup.select("a[href]"):
        href = str(a.get("href") or "").strip()
        label = a.get_text(" ", strip=True)
        if not href or href.startswith("#"):
            continue
        low = f"{href} {label}".lower()
        if re.search(r"download|getfile|/file/|attach|\.(pdf|docx?|xlsx?|zip|rar)(\?|$)", low):
            if "документы и реквизиты" in label.lower():
                continue
            doc_links.append({"name": label or "document", "url": urljoin(root + "/", href)})

    description = None
    for ln in lines:
        if len(ln) > 80 and not re.search(r"cookie|javascript", ln, re.I):
            description = ln[:2000]
            break

    return {
        "title": title,
        "deadline_msk": deadline,
        "customer_name": customer,
        "status": status,
        "description": description,
        "doc_links": doc_links,
        "card_fetched": True,
        "url": None,
    }


def probe_session(
    site: RtsMarketSite,
    path: Path | None = None,
    base_url_arg: str | None = None,
    *,
    on_retry=None,
) -> str:
    """ok | missing | expired | blocked."""
    cookies_file = path or cookies_path(site)
    if not cookies_file.is_file():
        return "missing"
    try:
        cookies = _cookie_dict(site, cookies_file)
        if not cookies:
            return "missing"
        root = (base_url_arg or base_url(site)).rstrip("/")
        with httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
            cookies=cookies,
            follow_redirects=True,
            timeout=60.0,
        ) as client:
            response = _market_request(
                client,
                "GET",
                f"{root}{LIST_PATH}",
                cookies=cookies,
                on_retry=on_retry,
            )
            if _is_captcha_response(response):
                return "blocked"
            if response.status_code in {401, 403}:
                return "expired"
            final = str(response.url).lower()
            if "/personal/auth" in final or "/login" in final:
                return "expired"
            text = response.text.lower()
            if "logout" in text or "личный кабинет" in text:
                return "ok"
            if response.status_code == 200 and any(m in text for m in site.probe_markers):
                return "ok"
            return "expired"
    except Exception:  # noqa: BLE001
        return "expired"


def _next_page(soup: BeautifulSoup, current: int) -> int | None:
    for a in soup.select("a[href]"):
        href = str(a.get("href") or "")
        label = a.get_text(" ", strip=True)
        m = re.search(r"[?&]page=(\d+)", href)
        if m:
            page = int(m.group(1))
            if page == current + 1:
                return page
        if label.isdigit() and int(label) == current + 1 and "page=" in href:
            return current + 1
        if re.search(r"следующ|далее|>", label, re.I) and m:
            return int(m.group(1))
    return None


def scrape_list_page(
    site: RtsMarketSite,
    *,
    keyword: str,
    base: str | None = None,
    page: int = 1,
    client: httpx.Client | None = None,
    cookies_file: Path | None = None,
    on_retry=None,
) -> tuple[list[dict], BeautifulSoup | None]:
    root = (base or base_url(site)).rstrip("/")
    own = client is None
    if own:
        client = httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
            cookies=_cookie_dict(site, cookies_file) or None,
            follow_redirects=True,
            timeout=60.0,
        )
    assert client is not None
    try:
        url = f"{root}{LIST_PATH}?{urlencode(list_query_params(keyword, page=page))}"
        jar = _cookie_dict(site, cookies_file) if cookies_file else dict(client.cookies)
        response = _market_request(
            client, "GET", url, cookies=jar, on_retry=on_retry
        )
        if _is_captcha_response(response):
            raise AuthError(f"{site.platform_id}_captcha_blocked")
        if response.status_code in {401, 403}:
            raise AuthError(f"{site.platform_id}_session_expired")
        if not relay_configured():
            response.raise_for_status()
        rows = parse_list_html(response.text, site=site, base=root)
        soup = BeautifulSoup(response.text, "lxml")
        return [asdict(r) for r in rows], soup
    finally:
        if own:
            client.close()


def scrape_queries(
    site: RtsMarketSite,
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

    root = (base or base_url(site)).rstrip("/")
    cap = None if int(limit or 0) <= 0 else int(limit)
    progress_total = cap if cap is not None else 0
    combined: list[dict] = []
    seen: set[str] = set()
    jar = _cookie_dict(site, cookies_file) if cookies_file else _cookie_dict(site)
    own = client is None
    if own:
        client = httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
            cookies=jar or None,
            follow_redirects=True,
            timeout=60.0,
        )
    assert client is not None
    try:
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
                batch, soup = scrape_list_page(
                    site,
                    keyword=q,
                    base=root,
                    page=page,
                    client=client,
                    cookies_file=cookies_file,
                    on_retry=on_retry,
                )
                if not batch:
                    break
                new = 0
                for row in batch:
                    tid = str(row.get("tender_id") or "")
                    if not tid or tid in seen:
                        continue
                    seen.add(tid)
                    row["url"] = card_url(site, tid, base=root)
                    combined.append(row)
                    new += 1
                    if cap is not None and len(combined) >= cap:
                        break
                if on_progress:
                    on_progress(len(combined), progress_total)
                if new == 0:
                    break
                nxt = _next_page(soup, page) if soup is not None else None
                if nxt is None:
                    break
                page = nxt
                if delay_s > 0:
                    time.sleep(delay_s)
        out = combined if cap is None else combined[:cap]
        return filter_rows_by_exclude(out, exclude)
    finally:
        if own:
            client.close()


def enrich_cards(
    site: RtsMarketSite,
    rows: list[dict],
    card_ids: list[str],
    *,
    base: str | None = None,
    cookies_file: Path | None = None,
    delay_s: float = 0.2,
    should_stop=None,
    on_progress=None,
    on_retry=None,
    client: httpx.Client | None = None,
) -> tuple[list[dict], list[dict]]:
    root = (base or base_url(site)).rstrip("/")
    by_id = {str(r.get("tender_id") or ""): r for r in rows}
    errors: list[dict] = []
    jar = _cookie_dict(site, cookies_file) if cookies_file else _cookie_dict(site)
    own = client is None
    if own:
        client = httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
            cookies=jar or None,
            follow_redirects=True,
            timeout=60.0,
        )
    assert client is not None
    try:
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
                        key = candidate
                        break
            if row is None:
                errors.append({"tender_id": raw_id, "error": "missing_in_scored"})
                continue
            native = key.split(":", 1)[-1]
            url = card_url(site, native, base=root)
            row["url"] = url
            try:
                jar = _cookie_dict(site, cookies_file) if cookies_file else dict(client.cookies)
                response = _market_request(
                    client, "GET", url, cookies=jar, on_retry=on_retry
                )
                if _is_captcha_response(response):
                    errors.append({"tender_id": key, "error": "captcha_blocked"})
                    row["card_error"] = "captcha_blocked"
                    continue
                if response.status_code in {401, 403}:
                    errors.append({"tender_id": key, "error": "http_403"})
                    row["card_error"] = "http_403"
                    continue
                response.raise_for_status()
                parsed = parse_card_html(
                    response.text, title_hint=str(row.get("title") or ""), base=root
                )
                for field, value in parsed.items():
                    if field == "url" or value is None:
                        continue
                    row[field] = value
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

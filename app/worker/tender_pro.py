"""Tender.Pro list + public card scrape (httpx + BeautifulSoup). No Playwright / JSON-RPC."""
from __future__ import annotations

import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.worker.http_retry import request_with_retry
from app.worker.list_scrape import AuthError, UA
from app.worker.platform_ids import PLATFORM_TENDER_PRO, compose_tender_id

DEFAULT_BASE = "https://www2.tender.pro"
VIEW_PATH = "/api/tender/{id}/view_public"
LIST_PATH = "/api/tenders/list"
POOL_LIMIT = 0  # 0 = no product cap (P11)
MAX_PAGES = 500
_ID_IN_HREF = re.compile(r"/api/tender/(\d+)/view_public", re.I)
_TOTAL_ROWS = re.compile(r"всего\s+строк\s*:\s*(\d+)", re.I)
_DEADLINE = re.compile(
    r"(?:При[её]м заявок до|Окончание|до)\s*:?\s*(\d{2}\.\d{2}\.\d{4}(?:\s+\d{1,2}:\d{2})?)",
    re.I,
)
_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class TenderProRow:
    tender_id: str  # native numeric id until prefix_rows
    title: str
    url: str
    price_rub: str | None = None
    location: str | None = None
    customer_name: str | None = None
    deadline_msk: str | None = None
    status: str | None = "Открыт"


def cookies_path() -> Path:
    raw = os.getenv("TENDER_PRO_COOKIES_FILE", "./cookies.tender-pro.txt").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path


def list_query_params(good_name: str, *, page: int = 1, by: int = 25) -> dict[str, str]:
    return {
        "good_name": good_name,
        "tender_state": "1",
        "country": "1",
        "region": "0_0",
        "tender_type": "100",
        "tender_show_own": "0",
        "basis": "1",
        "tender_promoter": "1",
        "tender_officer": "0",
        "by": str(by),
        "order": "1",
        "page": str(max(1, page)),
    }


def parse_list_html(html: str, *, base_url: str = DEFAULT_BASE) -> tuple[list[TenderProRow], int | None]:
    soup = BeautifulSoup(html, "lxml")
    total: int | None = None
    m_total = _TOTAL_ROWS.search(soup.get_text(" ", strip=True))
    if m_total:
        total = int(m_total.group(1))

    rows: list[TenderProRow] = []
    seen: set[str] = set()
    for tr in soup.select("tr.table-stat__row"):
        link = tr.select_one('a[href*="/api/tender/"][href*="view_public"]')
        if link is None:
            link = tr.find("a", href=_ID_IN_HREF)
        if link is None:
            continue
        href = str(link.get("href") or "")
        m = _ID_IN_HREF.search(href)
        if not m:
            continue
        native = m.group(1)
        if native in seen:
            continue
        seen.add(native)
        title = link.get_text(" ", strip=True) or f"Tender {native}"
        text = tr.get_text(" ", strip=True)
        deadline = None
        dm = _DEADLINE.search(text)
        if dm:
            deadline = dm.group(1).strip()
        rows.append(
            TenderProRow(
                tender_id=native,
                title=title,
                url=urljoin(base_url, href if href.startswith("/") else VIEW_PATH.format(id=native)),
                deadline_msk=deadline,
                status="Открыт",
            )
        )
    return rows, total


def parse_card_html(html: str, *, title_hint: str = "") -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n", strip=True)
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    title = title_hint
    h1 = soup.find(["h1", "h2"])
    if h1:
        title = h1.get_text(" ", strip=True) or title

    deadline = None
    dm = _DEADLINE.search(text)
    if dm:
        deadline = dm.group(1).strip()

    status = None
    for ln in lines[:60]:
        if re.search(r"Открыт|При[её]м заявок|Завершен|Закрыт", ln, re.I):
            status = ln
            break

    goods: list[str] = []
    capture = False
    for ln in lines:
        if re.search(r"^Товары$", ln, re.I):
            capture = True
            continue
        if capture:
            if re.search(r"^(Документы|Общая информация|Участники)$", ln, re.I):
                break
            if ln and not re.search(r"зарегистрироваться", ln, re.I):
                goods.append(ln)
    goods_blob = " ".join(goods[:40])

    doc_links: list[dict[str, str]] = []
    for a in soup.select("a[href]"):
        href = str(a.get("href") or "").strip()
        label = a.get_text(" ", strip=True)
        if not href or href.startswith("#"):
            continue
        if re.search(r"download|getfile|/file/|\.(pdf|docx?|xlsx?|zip)(\?|$)", href, re.I) or (
            label and re.search(r"\.(pdf|docx?|xlsx?|zip)$", label, re.I)
        ):
            if re.search(r"зарегистрироваться", label, re.I):
                continue
            doc_links.append({"name": label or "document", "url": urljoin(DEFAULT_BASE, href)})

    return {
        "title": title,
        "deadline_msk": deadline,
        "status": status,
        "description": goods_blob or None,
        "fit_extra": goods_blob,
        "doc_links": doc_links,
        "card_fetched": True,
    }


def probe_tender_pro_cookies(
    path: Path | None = None,
    base_url: str = DEFAULT_BASE,
    *,
    on_retry=None,
) -> str:
    """ok | missing | expired — list endpoint probe (P14)."""
    cookies_file = path or cookies_path()
    if not cookies_file.is_file():
        return "missing"
    try:
        with httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
            follow_redirects=True,
            timeout=60.0,
        ) as client:
            url = urljoin(base_url, LIST_PATH)
            response = request_with_retry(
                client,
                "GET",
                url,
                params=list_query_params("probe", page=1, by=1),
                on_retry=on_retry,
            )
            if response.status_code == 403:
                return "expired"
            response.raise_for_status()
        return "ok"
    except Exception:  # noqa: BLE001
        return "expired"


def scrape_list_page(
    *,
    good_name: str,
    base_url: str = DEFAULT_BASE,
    page: int = 1,
    by: int = 25,
    client: httpx.Client | None = None,
    on_retry=None,
) -> tuple[list[dict], int | None]:
    own = client is None
    if own:
        client = httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
            follow_redirects=True,
            timeout=60.0,
        )
    assert client is not None
    try:
        url = urljoin(base_url, LIST_PATH)
        response = request_with_retry(
            client,
            "GET",
            url,
            params=list_query_params(good_name, page=page, by=by),
            on_retry=on_retry,
        )
        rows, total = parse_list_html(response.text, base_url=base_url)
        return [asdict(r) for r in rows], total
    finally:
        if own:
            client.close()


def scrape_queries(
    *,
    queries: list[str],
    limit: int = POOL_LIMIT,
    base_url: str = DEFAULT_BASE,
    should_stop=None,
    on_progress=None,
    on_retry=None,
    client: httpx.Client | None = None,
    delay_s: float = 0.15,
    exclude: list[str] | None = None,
) -> list[dict]:
    """Union of good_name searches, deduped by native id; soft-capped only if limit > 0."""
    from app.worker.exclude_filter import filter_rows_by_exclude

    cap = None if int(limit or 0) <= 0 else int(limit)
    progress_total = cap if cap is not None else 0
    combined: list[dict] = []
    seen: set[str] = set()
    own = client is None
    if own:
        client = httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
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
            page = 1
            while page <= MAX_PAGES and (cap is None or len(combined) < cap):
                if should_stop and should_stop():
                    break
                batch, total = scrape_list_page(
                    good_name=str(query).strip(),
                    base_url=base_url,
                    page=page,
                    client=client,
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
                    combined.append(row)
                    new += 1
                    if cap is not None and len(combined) >= cap:
                        break
                if on_progress:
                    on_progress(len(combined), progress_total)
                if new == 0:
                    break
                if total is not None and page * 25 >= total:
                    break
                if len(batch) < 25:
                    break
                page += 1
                if delay_s > 0:
                    time.sleep(delay_s)
        if cap is None:
            out = combined
        else:
            out = combined[:cap]
        return filter_rows_by_exclude(out, exclude)
    finally:
        if own:
            client.close()


def enrich_cards(
    rows: list[dict],
    card_ids: list[str],
    *,
    base_url: str = DEFAULT_BASE,
    delay_s: float = 0.2,
    should_stop=None,
    on_progress=None,
    on_retry=None,
    client: httpx.Client | None = None,
) -> tuple[list[dict], list[dict]]:
    """Fetch public cards for L1–L3. card_ids may be prefixed or native."""
    by_id = {str(r.get("tender_id") or ""): r for r in rows}
    native_of = {}
    for tid in list(by_id):
        if ":" in tid:
            native_of[tid.split(":", 1)[1]] = tid
        else:
            native_of[tid] = tid

    errors: list[dict] = []
    own = client is None
    if own:
        client = httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
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
            if row is None and ":" in key:
                row = by_id.get(key)
            if row is None:
                # card_ids are prefixed; rows may already be prefixed
                for candidate in by_id:
                    if candidate == key or candidate.endswith(":" + key.split(":")[-1]):
                        row = by_id[candidate]
                        key = candidate
                        break
            if row is None:
                errors.append({"tender_id": raw_id, "error": "missing_in_scored"})
                continue
            native = key.split(":", 1)[-1]
            url = str(row.get("url") or urljoin(base_url, VIEW_PATH.format(id=native)))
            try:
                response = request_with_retry(client, "GET", url, on_retry=on_retry)
                if response.status_code == 403:
                    errors.append({"tender_id": key, "error": "http_403"})
                    row["card_error"] = "http_403"
                    continue
                response.raise_for_status()
                parsed = parse_card_html(response.text, title_hint=str(row.get("title") or ""))
                row.update({k: v for k, v in parsed.items() if v is not None})
                # Prefer goods text for scoring bump already done; keep title
                if parsed.get("fit_extra") and not row.get("title"):
                    row["title"] = parsed["fit_extra"][:200]
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
    return compose_tender_id(PLATFORM_TENDER_PRO, native_id)

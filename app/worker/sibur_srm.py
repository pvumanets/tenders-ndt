"""Sibur SRM (srm.sibur.ru) list via SAP NWBC POWL + Playwright."""
from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.worker.cookies import parse_netscape_cookies
from app.worker.list_scrape import AuthError
from app.worker.platform_ids import PLATFORM_SIBUR_SRM, compose_tender_id
from app.worker.playwright_cookies import netscape_to_playwright

DEFAULT_BASE = "https://srm.sibur.ru"
DEFAULT_NWBC_NODE = "0000000037"
POOL_LIMIT = 0
_REPO_ROOT = Path(__file__).resolve().parents[2]
_LOGIN_TITLE = "вход в систему"
_LOGIN_BODY_MARKERS = ("пользователь", "пароль", "забыли пароль")
_PROC_ID = re.compile(r"\b(\d{6,8})\b")
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class SiburRow:
    tender_id: str
    title: str
    url: str
    customer_name: str | None = None
    deadline_msk: str | None = None
    status: str | None = None


def cookies_path() -> Path:
    raw = os.getenv("SIBUR_COOKIES_FILE", "./cookies.sibur.txt").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path


def cookies_present() -> bool:
    path = cookies_path()
    if not path.is_file():
        return False
    try:
        return bool(parse_netscape_cookies(path))
    except OSError:
        return False


def base_url() -> str:
    return (os.getenv("SIBUR_BASE_URL") or DEFAULT_BASE).rstrip("/")


def nwbc_node() -> str:
    return (os.getenv("SIBUR_NWBC_NODE") or DEFAULT_NWBC_NODE).strip()


def nwbc_search_url(*, base: str | None = None, node: str | None = None) -> str:
    root = (base or base_url()).rstrip("/")
    n = node or nwbc_node()
    return f"{root}/ui2/nwbc/?sap-nwbc-node={n}"


def card_url(native_id: str, *, base: str | None = None) -> str:
    return nwbc_search_url(base=base) + f"#proc-{str(native_id).strip()}"


def is_login_page(*, title: str, body: str) -> bool:
    t = (title or "").strip().lower()
    b = (body or "").lower()
    if _LOGIN_TITLE in t:
        return True
    if "вход в систему" in b and any(m in b for m in _LOGIN_BODY_MARKERS):
        return True
    if "выход из системы выполнен успешно" in b:
        return True
    return False


def parse_grid_text(text: str, *, base: str | None = None) -> list[SiburRow]:
    """Parse POWL grid plain text — procedure id + line as title."""
    root = (base or base_url()).rstrip("/")
    rows: list[SiburRow] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = " ".join(raw.split())
        if len(line) < 12:
            continue
        m = _PROC_ID.search(line)
        if not m:
            continue
        native = m.group(1)
        if native in seen or native == "000000":
            continue
        if not re.search(r"[A-Za-zА-Яа-я]", line):
            continue
        seen.add(native)
        rows.append(
            SiburRow(
                tender_id=native,
                title=line[:500],
                url=card_url(native, base=root),
            )
        )
    return rows


def _playwright_timeout_ms() -> float:
    raw = (os.getenv("SIBUR_PLAYWRIGHT_TIMEOUT_MS") or "90000").strip()
    try:
        return float(raw)
    except ValueError:
        return 90000.0


def _headless() -> bool:
    return (os.getenv("SIBUR_HEADLESS") or "1").strip().lower() not in {
        "0",
        "false",
        "no",
    }


def _powl_frame(page: Any) -> Any:
    for frame in page.frames:
        url = str(frame.url or "").lower()
        if "webdynpro/sap/powl" in url or "zsapsrm_b_rfxandauctions" in url:
            return frame
    return page


def _page_session_probe(page: Any, *, url: str) -> str:
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    title = page.title()
    body = page.inner_text("body")
    if is_login_page(title=title, body=body):
        return "expired"
    return "ok"


def _page_scrape_rows(page: Any, *, url: str, base: str) -> list[SiburRow]:
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    title = page.title()
    body = page.inner_text("body")
    if is_login_page(title=title, body=body):
        raise AuthError("sibur-srm_session_expired")
    frame = _powl_frame(page)
    try:
        frame.wait_for_selector("table tr, div[class*='lsST']", timeout=int(_playwright_timeout_ms()))
    except Exception:
        pass
    chunks: list[str] = [body]
    try:
        chunks.append(frame.inner_text("body"))
    except Exception:
        pass
    for tr in frame.locator("table tr").all()[:200]:
        try:
            chunks.append(tr.inner_text())
        except Exception:
            continue
    combined = "\n".join(chunks)
    return parse_grid_text(combined, base=base)


def probe_sibur_session(
    path: Path | None = None,
    base_url_arg: str | None = None,
    *,
    on_retry=None,
) -> str:
    """ok | missing | expired."""
    cookies_file = path or cookies_path()
    if not cookies_file.is_file():
        return "missing"
    try:
        jar = netscape_to_playwright(cookies_file)
        if not jar:
            return "missing"
    except OSError:
        return "missing"
    root = (base_url_arg or base_url()).rstrip("/")
    url = nwbc_search_url(base=root)
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=_headless())
            context = browser.new_context(locale="ru-RU", user_agent=_UA)
            context.add_cookies(jar)
            page = context.new_page()
            page.set_default_timeout(_playwright_timeout_ms())
            result = _page_session_probe(page, url=url)
            browser.close()
            return result
    except Exception:  # noqa: BLE001
        return "expired"


def _row_matches_queries(row: SiburRow, queries: list[str]) -> bool:
    if not queries:
        return True
    hay = row.title.lower()
    return any(q.lower() in hay for q in queries if q.strip())


def scrape_queries(
    *,
    queries: list[str],
    limit: int = POOL_LIMIT,
    base: str | None = None,
    cookies_file: Path | None = None,
    exclude: list[str] | None = None,
    should_stop=None,
    on_progress=None,
    on_retry=None,
    delay_s: float = 0.0,
) -> list[dict]:
    from app.worker.exclude_filter import filter_rows_by_exclude

    root = (base or base_url()).rstrip("/")
    jar_path = cookies_file or cookies_path()
    if not jar_path.is_file():
        raise AuthError("sibur-srm_missing_cookies")
    jar = netscape_to_playwright(jar_path)
    if not jar:
        raise AuthError("sibur-srm_missing_cookies")
    cap = None if int(limit or 0) <= 0 else int(limit)
    url = nwbc_search_url(base=root)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=_headless())
        context = browser.new_context(locale="ru-RU", user_agent=_UA)
        context.add_cookies(jar)
        page = context.new_page()
        page.set_default_timeout(_playwright_timeout_ms())
        if should_stop and should_stop():
            browser.close()
            return []
        parsed = _page_scrape_rows(page, url=url, base=root)
        browser.close()
    q = [str(x).strip() for x in queries if str(x).strip()]
    filtered = [r for r in parsed if _row_matches_queries(r, q)]
    if cap is not None:
        filtered = filtered[:cap]
    if on_progress:
        on_progress(len(filtered), cap or len(filtered))
    rows = [asdict(r) for r in filtered]
    return filter_rows_by_exclude(rows, exclude)


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
) -> tuple[list[dict], list[dict]]:
    """POWL list carries titles; card enrich is no-op v1."""
    total = len(card_ids)
    if on_progress:
        on_progress(total, total)
    return rows, []


def compose_tender_id_sibur(native_id: str) -> str:
    return compose_tender_id(PLATFORM_SIBUR_SRM, native_id)

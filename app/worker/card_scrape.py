"""P3: enrich L1–L3 rows by fetching tender card HTML (httpx)."""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.worker.cookies import parse_netscape_cookies
from app.worker.customer_name import clean_customer_name
from app.worker.docs import sanitize_filename
from app.worker.list_scrape import AuthError, UA

_FILE_EXT = re.compile(
    r"\.(pdf|docx?|xlsx?|pptx?|zip|rar|7z|rtf|odt|ods|csv|txt|sig|xml)(\?|$)",
    re.I,
)
_HREF_DOWNLOAD = re.compile(r"download|getfile|get-file|/file/|/files/|/docs?/", re.I)
_ARCHIVE_TEXT = re.compile(r"скачать одним архивом", re.I)
_SKIP_HREF = re.compile(r"^(javascript:|mailto:|#)", re.I)

METHOD_PATTERNS = [
    ("УЗК", re.compile(r"ультразвуков|узк|\bук\b|узт", re.I)),
    ("РК", re.compile(r"радиограф|\bрк\b|гаммаграф|рентген", re.I)),
    ("ЦР", re.compile(r"цифров\w*\s+радиограф|\bцр\b", re.I)),
    ("ВИК", re.compile(r"\bвик\b|визуальн\w*\s+и\s+измерительн", re.I)),
    ("ПВК", re.compile(r"\bпвк\b|капиллярн|цветн\w*\s+дефектоскоп|проникающ", re.I)),
    ("НК", re.compile(r"неразрушающ|\bнк\b", re.I)),
]


def _cookie_dict(path: Path) -> dict[str, str]:
    return {c["name"]: c["value"] for c in parse_netscape_cookies(path)}


def _lines(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    return [ln.strip() for ln in soup.get_text("\n", strip=True).split("\n") if ln.strip()]


def _after(lines: list[str], *labels: str) -> str | None:
    for i, ln in enumerate(lines):
        for lab in labels:
            if ln == lab or ln.startswith(lab + " ") or ln.startswith(lab + ","):
                if i + 1 < len(lines):
                    return lines[i + 1]
    return None


def _detect_methods(text: str) -> str:
    found: list[str] = []
    for name, rx in METHOD_PATTERNS:
        if rx.search(text) and name not in found:
            found.append(name)
    return ", ".join(found) if found else ""


def parse_card_html(html: str, title_hint: str = "") -> dict[str, Any]:
    if "403 Forbidden" in html and "administrative rules" in html:
        raise AuthError("WAF/403 on card page")
    lines = _lines(html)
    blob = "\n".join(lines)

    status = None
    for ln in lines[:80]:
        if re.search(r"При[её]м заявок|Завершен|Отменен|Подведен", ln, re.I):
            status = ln
            break

    deadline = _after(lines, "Окончание (МСК)", "Окончание MSK", "Окончание")
    # Sometimes value is date only on next line after label with time elsewhere
    if deadline and re.match(r"\d{2}\.\d{2}\.\d{4}", deadline):
        # look for time on same/nearby
        pass

    inn = _after(lines, "ИНН")
    if inn and not re.fullmatch(r"\d{10,12}", inn):
        m = re.search(r"\b(\d{10,12})\b", inn)
        inn = m.group(1) if m else None
    # Prefer customer block INN: first ИНН after «Заказчик» section often correct;
    # keep first 10–12 digit match in page near Заказчик
    inns = re.findall(r"ИНН\s*(\d{10,12})", blob)
    if inns:
        inn = inns[0]

    kpp = None
    kpps = re.findall(r"КПП\s*(\d{9})", blob)
    if kpps:
        kpp = kpps[0]

    contact_name = _after(lines, "Контактное лицо")
    phone = _after(lines, "Телефон")
    email = None
    for ln in lines:
        if "@" in ln and "." in ln and " " not in ln.strip():
            email = ln.strip()
            break
        m = re.search(r"[\w.+-]+@[\w.-]+\.\w+", ln)
        if m and "example" not in m.group(0):
            email = m.group(0)
            break

    location = _after(lines, "Место поставки")
    customer = _after(lines, "Заказчик")
    if customer == "Наименование":
        # next line after Наименование under Заказчик block
        for i, ln in enumerate(lines):
            if ln == "Заказчик" and i + 2 < len(lines) and lines[i + 1] == "Наименование":
                customer = lines[i + 2]
                break

    price = _after(lines, "Начальная цена", "Начальная цена, ₽", "Начальная цена,₽")
    if price and "₽" not in price and re.search(r"\d", price):
        # sometimes split
        pass

    source_etp = None
    for i, ln in enumerate(lines):
        if ln in ("ТЭК-Торг", "ЭТП ГПБ", "B2B-Center", "РТС-тендер", "ЕИС") or (
            "торг" in ln.lower() and len(ln) < 40
        ):
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if nxt and len(nxt) < 40 and not nxt.startswith("Подача"):
                source_etp = f"{ln} {nxt}".strip()
            else:
                source_etp = ln
            break

    methods = _detect_methods(title_hint + "\n" + blob[:2000])

    return {
        "status": status,
        "deadline_msk": deadline,
        "customer_inn": inn,
        "customer_kpp": kpp,
        "contact_name": contact_name,
        "contact_phone": phone,
        "contact_email": email,
        "location": location or None,
        "customer_name": clean_customer_name(customer),
        "price_rub": price if price and re.search(r"\d", price or "") else None,
        "source_etp": source_etp,
        "methods": methods or None,
    }


def _looks_like_file_href(href: str) -> bool:
    path = urlparse(href).path or href
    return bool(_HREF_DOWNLOAD.search(href) or _FILE_EXT.search(path))


def parse_document_links(html: str, page_url: str) -> list[dict[str, str]]:
    """Collect per-file download links; fall back to «Скачать одним архивом»."""
    soup = BeautifulSoup(html, "lxml")
    files: list[dict[str, str]] = []
    archive: dict[str, str] | None = None
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href") or "").strip()
        if not href or _SKIP_HREF.search(href):
            continue
        absolute = urljoin(page_url, href)
        if absolute in seen or absolute.rstrip("/") == page_url.rstrip("/"):
            continue
        text = " ".join(anchor.get_text(" ", strip=True).split())
        if _ARCHIVE_TEXT.search(text) or _ARCHIVE_TEXT.search(href):
            seen.add(absolute)
            archive = {"name": "docs.zip", "url": absolute}
            continue
        if not _looks_like_file_href(href) and not _FILE_EXT.search(text):
            continue
        seen.add(absolute)
        name = sanitize_filename(text) or sanitize_filename(urlparse(absolute).path) or "document"
        if not _FILE_EXT.search(name) and _FILE_EXT.search(urlparse(absolute).path):
            ext = Path(urlparse(absolute).path).suffix
            name = f"{name}{ext}"
        files.append({"name": name, "url": absolute})
    if files:
        return files
    return [archive] if archive else []


def apply_card_fields(row: dict[str, Any], fields: dict[str, Any]) -> None:
    """Merge P3 card fields onto a list row. Clean card customer_name always wins."""
    for key, value in fields.items():
        if not value:
            continue
        if key == "customer_name":
            cleaned = clean_customer_name(value)
            if cleaned:
                row[key] = cleaned
            continue
        existing = row.get(key)
        if key in ("location", "price_rub") and existing and existing not in (None, "—", ""):
            if key == "price_rub" and existing == "—":
                row[key] = value
            elif key == "location" and "Russia" in str(existing):
                row[key] = value
            continue
        row[key] = value


def enrich_cards(
    rows: list[dict],
    card_ids: list[str],
    *,
    cookies_path: Path,
    delay_s: float = 0.25,
    should_stop=None,
    on_progress=None,
) -> tuple[list[dict], list[dict]]:
    """Return (enriched_rows, errors). Mutates copies of L1–L3 rows."""
    id_set = set(card_ids)
    by_id = {r["tender_id"]: r for r in rows}
    errors: list[dict] = []
    auth_fails = 0

    cookies = _cookie_dict(cookies_path)
    if not cookies:
        raise AuthError(f"No cookies in {cookies_path}")

    with httpx.Client(
        headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
        cookies=cookies,
        follow_redirects=True,
        timeout=60.0,
    ) as client:
        for i, tid in enumerate(card_ids, start=1):
            if should_stop and should_stop():
                break
            row = by_id.get(tid)
            if not row:
                errors.append({"tender_id": tid, "error": "missing_in_scored"})
                continue
            url = row.get("url")
            if not url:
                row["card_error"] = "no_url"
                errors.append({"tender_id": tid, "error": "no_url"})
                continue
            try:
                r = client.get(url)
                if r.status_code == 403 or (
                    "403 Forbidden" in r.text and "administrative rules" in r.text
                ):
                    auth_fails += 1
                    row["card_error"] = "http_403"
                    errors.append({"tender_id": tid, "error": "http_403"})
                    if auth_fails >= 5:
                        raise AuthError("Too many 403 on card pages — stop")
                else:
                    r.raise_for_status()
                    fields = parse_card_html(r.text, title_hint=row.get("title") or "")
                    links = parse_document_links(r.text, url)
                    if links:
                        row["doc_links"] = links
                    apply_card_fields(row, fields)
                    row.pop("card_error", None)
                    row["card_fetched"] = True
            except AuthError:
                raise
            except Exception as e:  # noqa: BLE001
                row["card_error"] = f"{type(e).__name__}: {e}"
                errors.append({"tender_id": tid, "error": row["card_error"]})
            if on_progress:
                on_progress(i, len(card_ids))
            if i % 50 == 0:
                print(f"cards {i}/{len(card_ids)}…")
            time.sleep(delay_s)

    # ensure every L1–L3 has either card_fetched or card_error
    for r in rows:
        if r.get("tender_id") in id_set or r.get("tier") in ("L1", "L2", "L3"):
            if not r.get("card_fetched") and not r.get("card_error"):
                r["card_error"] = "not_attempted"

    return rows, errors

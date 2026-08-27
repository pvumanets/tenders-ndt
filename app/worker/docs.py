"""P5.5: download L1–L3 attachments to SCOUT_DOCS_DIR and upsert documents meta."""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import unquote
from uuid import uuid4

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.config import database_url
from app.db.models import Document, Lot
from app.db.session import session_factory
from app.worker.cookies import parse_netscape_cookies
from app.worker.ingest import INBOX_TIERS
from app.worker.list_scrape import AuthError, UA

MAX_FILE_BYTES = 50 * 1024 * 1024
_UNSAFE_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_TRUTHY = frozenset({"1", "true", "yes"})
_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class DocsDownloadResult:
    saved: int = 0
    skipped: int = 0
    errors: int = 0


def download_docs_enabled() -> bool:
    return os.environ.get("DOWNLOAD_DOCS", "0").strip().lower() in _TRUTHY


def docs_dir() -> Path:
    raw = os.environ.get("SCOUT_DOCS_DIR", "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else _REPO_ROOT / path
    return _REPO_ROOT / "data" / "docs"


from app.worker.platform_ids import volume_dir_name


def sanitize_filename(name: str | None) -> str | None:
    if not name:
        return None
    text = unquote(str(name)).replace("\\", "/").split("/")[-1].strip()
    text = _UNSAFE_NAME.sub("_", text).strip(" .")
    if not text or text in {".", ".."}:
        return None
    return text[:240]


def volume_relpath(tender_id: str, filename: str) -> str:
    folder = volume_dir_name(tender_id)
    if folder is None:
        raise ValueError("invalid_tender_id")
    return f"{folder}/{filename}"


def resolve_volume_file(tender_id: str, filename: str, *, root: Path | None = None) -> Path | None:
    folder = volume_dir_name(tender_id)
    safe_name = sanitize_filename(filename)
    if folder is None or safe_name is None:
        return None
    if safe_name != filename:
        return None
    base = (root or docs_dir()).resolve()
    target = (base / folder / safe_name).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        return None
    return target if target.is_file() else None


def filename_from_content_disposition(header: str | None, fallback: str) -> str:
    if not header:
        return fallback
    message = EmailMessage()
    message["content-disposition"] = header
    params = message.get_params() or []
    by_key = {str(key).lower(): value for key, value in params if key}
    star = by_key.get("filename*")
    if isinstance(star, str) and "''" in star:
        _, encoded = star.split("''", 1)
        safe = sanitize_filename(unquote(encoded))
        if safe:
            return safe
    plain = message.get_filename()
    safe = sanitize_filename(plain) if plain else None
    return safe or fallback


def _cookie_dict(path: Path) -> dict[str, str]:
    return {c["name"]: c["value"] for c in parse_netscape_cookies(path)}


def _is_html_payload(content_type: str, body_prefix: bytes) -> bool:
    if "text/html" in (content_type or "").lower():
        return True
    head = body_prefix[:200].lstrip().lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html")


def _persist_document(*, tender_id: str, filename: str, size_bytes: int, relpath: str) -> None:
    if not database_url():
        return
    factory = session_factory()
    with factory() as session:
        lot = session.get(Lot, tender_id)
        if lot is None or lot.tier not in INBOX_TIERS:
            return
        stmt = pg_insert(Document).values(
            id=uuid4(),
            tender_id=tender_id,
            filename=filename,
            size_bytes=size_bytes,
            volume_path=relpath,
        )
        session.execute(
            stmt.on_conflict_do_update(
                constraint="uq_documents_lot_file",
                set_={"size_bytes": size_bytes, "volume_path": relpath},
            )
        )
        session.commit()


def _inbox_candidates(rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        tier = str(row.get("tier") or "").strip()
        if tier not in INBOX_TIERS:
            continue
        tender_id = str(row.get("tender_id") or "").strip()
        if not tender_id or tender_id in seen:
            continue
        seen.add(tender_id)
        out.append(row)
    return out


def _links_for_row(row: dict) -> list[dict[str, str]]:
    raw = row.get("doc_links") or []
    if not isinstance(raw, list):
        return []
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        name = sanitize_filename(str(item.get("name") or "")) or "document"
        if not url or url in seen:
            continue
        seen.add(url)
        links.append({"name": name, "url": url})
    return links


def download_inbox_docs(
    rows: list[dict],
    *,
    cookies_path: Path,
    docs_root: Path | None = None,
    delay_s: float = 0.2,
    should_stop=None,
    persist_meta: bool = True,
    client: httpx.Client | None = None,
) -> DocsDownloadResult:
    """Fetch attachments for score≥4 rows. No-op when DOWNLOAD_DOCS is off."""
    if not download_docs_enabled():
        return DocsDownloadResult()
    root = (docs_root or docs_dir()).resolve()
    candidates = _inbox_candidates(rows)
    saved = skipped = errors = 0
    auth_fails = 0
    own_client = client is None
    if own_client:
        cookies = _cookie_dict(cookies_path)
        if not cookies:
            raise AuthError(f"No cookies in {cookies_path}")
        client = httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
            cookies=cookies,
            follow_redirects=True,
            timeout=60.0,
        )
    assert client is not None
    try:
        for row in candidates:
            if should_stop and should_stop():
                break
            tender_id = str(row["tender_id"]).strip()
            folder = volume_dir_name(tender_id)
            if folder is None:
                errors += 1
                continue
            links = _links_for_row(row)
            if not links:
                continue
            used_names: set[str] = set()
            for index, link in enumerate(links, start=1):
                if should_stop and should_stop():
                    break
                fallback = sanitize_filename(link["name"]) or f"document-{index}"
                if fallback in used_names:
                    fallback = f"{Path(fallback).stem}-{index}{Path(fallback).suffix}"
                dest_name = fallback
                dest = root / folder / dest_name
                if dest.is_file():
                    skipped += 1
                    used_names.add(dest_name)
                    if persist_meta:
                        _persist_document(
                            tender_id=tender_id,
                            filename=dest_name,
                            size_bytes=dest.stat().st_size,
                            relpath=volume_relpath(tender_id, dest_name),
                        )
                    continue
                try:
                    with client.stream("GET", link["url"]) as response:
                        if response.status_code == 403:
                            auth_fails += 1
                            errors += 1
                            if auth_fails >= 5:
                                raise AuthError("Too many 403 on docs — stop")
                            continue
                        response.raise_for_status()
                        dest_name = filename_from_content_disposition(
                            response.headers.get("content-disposition"),
                            fallback,
                        )
                        if dest_name in used_names:
                            dest_name = f"{Path(dest_name).stem}-{index}{Path(dest_name).suffix}"
                        dest = root / folder / dest_name
                        if dest.is_file():
                            skipped += 1
                            used_names.add(dest_name)
                            if persist_meta:
                                _persist_document(
                                    tender_id=tender_id,
                                    filename=dest_name,
                                    size_bytes=dest.stat().st_size,
                                    relpath=volume_relpath(tender_id, dest_name),
                                )
                            continue
                        chunks = response.iter_bytes()
                        first = next(chunks, b"")
                        content_type = response.headers.get("content-type") or ""
                        if _is_html_payload(content_type, first):
                            errors += 1
                            continue
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        tmp = dest.with_name(dest.name + ".part")
                        written = len(first)
                        try:
                            with tmp.open("wb") as handle:
                                handle.write(first)
                                for chunk in chunks:
                                    written += len(chunk)
                                    if written > MAX_FILE_BYTES:
                                        raise ValueError("file_too_large")
                                    handle.write(chunk)
                            tmp.replace(dest)
                        except Exception:
                            if tmp.exists():
                                tmp.unlink(missing_ok=True)
                            raise
                    saved += 1
                    used_names.add(dest_name)
                    if persist_meta:
                        _persist_document(
                            tender_id=tender_id,
                            filename=dest_name,
                            size_bytes=written,
                            relpath=volume_relpath(tender_id, dest_name),
                        )
                except AuthError:
                    raise
                except Exception:  # noqa: BLE001
                    errors += 1
                time.sleep(delay_s)
    finally:
        if own_client:
            client.close()
    return DocsDownloadResult(saved=saved, skipped=skipped, errors=errors)

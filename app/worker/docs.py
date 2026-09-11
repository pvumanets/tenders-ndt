"""P5.5 / 094: after-AI zip download to SCOUT_DOCS_DIR + documents meta + docs_status."""
from __future__ import annotations

import io
import os
import re
import time
import zipfile
from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import unquote, urlparse
from uuid import uuid4

import httpx
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.config import database_url
from app.db.models import Document, Lot, LotState
from app.db.session import session_factory
from app.worker.fetch_guard import (
    FetchUrlDenied,
    allow_hosts,
    assert_fetch_url_allowed,
    cookies_jar_from_netscape,
    open_allowlisted_stream,
)
from app.worker.ingest import INBOX_TIERS
from app.worker.list_scrape import AuthError, UA
from app.worker.platform_ids import (
    PLATFORM_OILB2BCS,
    PLATFORM_SIBUR_SRM,
    split_tender_id,
    volume_dir_name,
)

MAX_FILE_BYTES = 50 * 1024 * 1024
ZIP_FILENAME = "docs.zip"
_UNSAFE_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_TRUTHY = frozenset({"1", "true", "yes"})
_REPO_ROOT = Path(__file__).resolve().parents[2]

DOC_STATUS_MISSING = "missing"
DOC_STATUS_PENDING_AI = "pending_ai"
DOC_STATUS_PENDING_DOWNLOAD = "pending_download"
DOC_STATUS_READY = "ready"
DOC_STATUS_EXTERNAL_ONLY = "external_only"
DOC_STATUS_UNSUPPORTED = "unsupported_platform"
DOC_STATUS_ERROR = "error"

UNSUPPORTED_DOC_PLATFORMS = frozenset({PLATFORM_OILB2BCS, PLATFORM_SIBUR_SRM})


@dataclass
class DocsPassResult:
    saved: int = 0
    skipped: int = 0
    errors: int = 0
    by_status: dict[str, int] = field(default_factory=dict)


# Back-compat alias used by cli / older tests
DocsDownloadResult = DocsPassResult


def download_docs_enabled() -> bool:
    return os.environ.get("DOWNLOAD_DOCS", "0").strip().lower() in _TRUTHY


def docs_dir() -> Path:
    raw = os.environ.get("SCOUT_DOCS_DIR", "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else _REPO_ROOT / path
    return _REPO_ROOT / "data" / "docs"


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


def _is_html_payload(content_type: str, body_prefix: bytes) -> bool:
    if "text/html" in (content_type or "").lower():
        return True
    head = body_prefix[:200].lstrip().lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html")


def link_url_allowed(url: str, allow: frozenset[str] | None = None) -> bool:
    try:
        assert_fetch_url_allowed(url, allow=allow)
        return True
    except FetchUrlDenied:
        return False


def _links_from_raw(raw: object) -> list[dict[str, str]]:
    if isinstance(raw, dict):
        items = raw.get("doc_links") or []
    else:
        items = raw or []
    if not isinstance(items, list):
        return []
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        name = sanitize_filename(str(item.get("name") or "")) or "document"
        if not url or url in seen:
            continue
        seen.add(url)
        links.append({"name": name, "url": url})
    return links


def split_doc_links(
    links: list[dict[str, str]], *, allow: frozenset[str] | None = None
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    allowed: list[dict[str, str]] = []
    external: list[dict[str, str]] = []
    hosts = allow if allow is not None else allow_hosts()
    for link in links:
        if link_url_allowed(link["url"], allow=hosts):
            allowed.append(link)
        else:
            external.append(link)
    return allowed, external


def _persist_zip_meta(*, tender_id: str, size_bytes: int) -> None:
    if not database_url():
        return
    factory = session_factory()
    with factory() as session:
        lot = session.get(Lot, tender_id)
        if lot is None or lot.tier not in INBOX_TIERS:
            return
        session.execute(delete(Document).where(Document.tender_id == tender_id))
        session.execute(
            pg_insert(Document)
            .values(
                id=uuid4(),
                tender_id=tender_id,
                filename=ZIP_FILENAME,
                size_bytes=size_bytes,
                volume_path=volume_relpath(tender_id, ZIP_FILENAME),
            )
            .on_conflict_do_update(
                constraint="uq_documents_lot_file",
                set_={
                    "size_bytes": size_bytes,
                    "volume_path": volume_relpath(tender_id, ZIP_FILENAME),
                },
            )
        )
        session.commit()


def _set_lot_docs_state(
    tender_id: str,
    *,
    status: str,
    external_url: str | None = None,
) -> None:
    if not database_url():
        return
    factory = session_factory()
    with factory() as session:
        state = session.get(LotState, tender_id)
        if state is None:
            state = LotState(tender_id=tender_id)
            session.add(state)
        state.docs_status = status
        state.docs_external_url = external_url
        session.commit()


def _fetch_bytes(client: httpx.Client, url: str, allow: frozenset[str]) -> tuple[bytes, str]:
    response = open_allowlisted_stream(client, url, allow=allow)
    try:
        if response.status_code == 403:
            raise AuthError("docs_http_403")
        response.raise_for_status()
        chunks = response.iter_bytes()
        first = next(chunks, b"")
        content_type = response.headers.get("content-type") or ""
        if _is_html_payload(content_type, first):
            raise ValueError("html_payload")
        buf = io.BytesIO()
        written = len(first)
        buf.write(first)
        for chunk in chunks:
            written += len(chunk)
            if written > MAX_FILE_BYTES:
                raise ValueError("file_too_large")
            buf.write(chunk)
        fallback = sanitize_filename(urlparse(url).path) or "document"
        name = filename_from_content_disposition(
            response.headers.get("content-disposition"),
            fallback,
        )
        return buf.getvalue(), name
    finally:
        response.close()


def _write_zip(dest: Path, members: list[tuple[str, bytes]]) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    used: set[str] = set()
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for index, (name, payload) in enumerate(members, start=1):
                safe = sanitize_filename(name) or f"document-{index}"
                if safe in used:
                    stem = Path(safe).stem
                    suffix = Path(safe).suffix
                    safe = f"{stem}-{index}{suffix}"
                used.add(safe)
                zf.writestr(safe, payload)
        tmp.replace(dest)
    except Exception:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise
    return dest.stat().st_size


def download_lot_zip(
    *,
    tender_id: str,
    links: list[dict[str, str]],
    platform_id: str | None,
    lot_url: str | None,
    cookies_path: Path,
    docs_root: Path | None = None,
    delay_s: float = 0.2,
    persist_meta: bool = True,
    client: httpx.Client | None = None,
    should_stop=None,
) -> str:
    """Download allowlisted links into docs.zip; return docs_status."""
    if platform_id in UNSUPPORTED_DOC_PLATFORMS:
        if persist_meta:
            _set_lot_docs_state(tender_id, status=DOC_STATUS_UNSUPPORTED)
        return DOC_STATUS_UNSUPPORTED

    folder = volume_dir_name(tender_id)
    if folder is None:
        if persist_meta:
            _set_lot_docs_state(tender_id, status=DOC_STATUS_ERROR)
        return DOC_STATUS_ERROR

    root = (docs_root or docs_dir()).resolve()
    dest = root / folder / ZIP_FILENAME
    hosts = allow_hosts()
    allowed, external = split_doc_links(links, allow=hosts)

    if not links:
        if persist_meta:
            _set_lot_docs_state(tender_id, status=DOC_STATUS_MISSING)
        return DOC_STATUS_MISSING

    if not allowed and external:
        ext = (lot_url or "").strip() or (external[0]["url"] if external else None)
        if persist_meta:
            _set_lot_docs_state(
                tender_id, status=DOC_STATUS_EXTERNAL_ONLY, external_url=ext
            )
        return DOC_STATUS_EXTERNAL_ONLY

    if not download_docs_enabled():
        if persist_meta:
            _set_lot_docs_state(tender_id, status=DOC_STATUS_PENDING_DOWNLOAD)
        return DOC_STATUS_PENDING_DOWNLOAD

    if dest.is_file():
        if persist_meta:
            _persist_zip_meta(tender_id=tender_id, size_bytes=dest.stat().st_size)
            _set_lot_docs_state(tender_id, status=DOC_STATUS_READY)
        return DOC_STATUS_READY

    if not allowed:
        if persist_meta:
            _set_lot_docs_state(tender_id, status=DOC_STATUS_MISSING)
        return DOC_STATUS_MISSING

    own_client = client is None
    if own_client:
        jar = cookies_jar_from_netscape(cookies_path)
        if not jar:
            raise AuthError(f"No cookies in {cookies_path}")
        client = httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
            cookies=jar,
            follow_redirects=False,
            timeout=60.0,
        )
    assert client is not None

    members: list[tuple[str, bytes]] = []
    try:
        for link in allowed:
            if should_stop and should_stop():
                break
            try:
                payload, name = _fetch_bytes(client, link["url"], hosts)
                members.append((name or link["name"], payload))
            except AuthError:
                raise
            except FetchUrlDenied:
                continue
            except Exception:  # noqa: BLE001
                continue
            time.sleep(delay_s)
    finally:
        if own_client:
            client.close()

    if not members:
        # Had allowlisted URLs but all failed — if externals exist, prefer external_only
        if external:
            ext = (lot_url or "").strip() or external[0]["url"]
            if persist_meta:
                _set_lot_docs_state(
                    tender_id, status=DOC_STATUS_EXTERNAL_ONLY, external_url=ext
                )
            return DOC_STATUS_EXTERNAL_ONLY
        if persist_meta:
            _set_lot_docs_state(tender_id, status=DOC_STATUS_ERROR)
        return DOC_STATUS_ERROR

    size = _write_zip(dest, members)
    if persist_meta:
        _persist_zip_meta(tender_id=tender_id, size_bytes=size)
        _set_lot_docs_state(tender_id, status=DOC_STATUS_READY)
    return DOC_STATUS_READY


def cookies_path_for_platform(platform_id: str | None) -> Path:
    """Resolve Netscape jar path for a platform (same env names as runner)."""
    from dotenv import load_dotenv

    load_dotenv(_REPO_ROOT / ".env")
    pid = (platform_id or "").strip() or "rostender"
    env_map = {
        "tender-pro": ("TENDER_PRO_COOKIES_FILE", "./cookies.tender-pro.txt"),
        "roseltorg": ("ROSELTORG_COOKIES_FILE", "./cookies.roseltorg.txt"),
        "b2b-center": ("B2B_CENTER_COOKIES_FILE", "./cookies.b2b-center.txt"),
        "rts-rosatom": ("RTS_ROSATOM_COOKIES_FILE", "./cookies.rts-rosatom.txt"),
        "oilb2bcs": ("OILB2BCS_COOKIES_FILE", "./cookies.oilb2bcs.txt"),
        "sibur-srm": ("SIBUR_COOKIES_FILE", "./cookies.sibur.txt"),
        "rostender": ("ROSTENDER_COOKIES_FILE", "./cookies.rostender.txt"),
    }
    env_name, default = env_map.get(pid, env_map["rostender"])
    raw = os.getenv(env_name, default)
    path = Path(raw)
    return path if path.is_absolute() else _REPO_ROOT / path


def finalize_docs_status_for_ids(
    tender_ids: list[str] | set[str],
    *,
    fallback: str = DOC_STATUS_ERROR,
) -> int:
    """Ensure each id has a non-empty docs_status. Returns how many rows were written."""
    ids = [str(x).strip() for x in tender_ids if str(x).strip()]
    if not ids or not database_url():
        return 0
    written = 0
    factory = session_factory()
    with factory() as session:
        for tid in ids:
            state = session.get(LotState, tid)
            if state is None:
                state = LotState(tender_id=tid)
                session.add(state)
            stored = (state.docs_status or "").strip()
            if stored:
                continue
            state.docs_status = fallback
            written += 1
        session.commit()
    return written


def run_docs_pass(
    tender_ids: list[str] | set[str],
    *,
    docs_root: Path | None = None,
    delay_s: float = 0.2,
    should_stop=None,
    persist_meta: bool = True,
) -> DocsPassResult:
    """After-AI docs pass: load lots from DB, write one zip each, set docs_status."""
    ids = [str(x).strip() for x in tender_ids if str(x).strip()]
    if not ids:
        return DocsPassResult()
    if not database_url():
        return DocsPassResult()

    factory = session_factory()
    result = DocsPassResult()
    with factory() as session:
        lots = list(session.scalars(select(Lot).where(Lot.tender_id.in_(ids))).all())

    by_platform: dict[str, list[Lot]] = {}
    for lot in lots:
        if lot.tier not in INBOX_TIERS:
            continue
        platform, _ = split_tender_id(lot.tender_id)
        pid = (lot.source_platform_id or platform or "rostender").strip()
        by_platform.setdefault(pid, []).append(lot)

    for platform_id, platform_lots in by_platform.items():
        if platform_id in UNSUPPORTED_DOC_PLATFORMS:
            for lot in platform_lots:
                if should_stop and should_stop():
                    break
                status = download_lot_zip(
                    tender_id=lot.tender_id,
                    links=[],
                    platform_id=platform_id,
                    lot_url=lot.url,
                    cookies_path=cookies_path_for_platform(platform_id),
                    docs_root=docs_root,
                    persist_meta=persist_meta,
                )
                result.by_status[status] = result.by_status.get(status, 0) + 1
            continue

        cookies = cookies_path_for_platform(platform_id)
        if not cookies.is_file():
            for lot in platform_lots:
                if persist_meta:
                    _set_lot_docs_state(lot.tender_id, status=DOC_STATUS_ERROR)
                result.errors += 1
                result.by_status[DOC_STATUS_ERROR] = (
                    result.by_status.get(DOC_STATUS_ERROR, 0) + 1
                )
            continue

        jar = cookies_jar_from_netscape(cookies)
        if not jar:
            for lot in platform_lots:
                if persist_meta:
                    _set_lot_docs_state(lot.tender_id, status=DOC_STATUS_ERROR)
                result.errors += 1
                result.by_status[DOC_STATUS_ERROR] = (
                    result.by_status.get(DOC_STATUS_ERROR, 0) + 1
                )
            continue

        with httpx.Client(
            headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"},
            cookies=jar,
            follow_redirects=False,
            timeout=60.0,
        ) as client:
            for index, lot in enumerate(platform_lots):
                if should_stop and should_stop():
                    break
                links = _links_from_raw(lot.raw)
                dest = (docs_root or docs_dir()).resolve() / (
                    volume_dir_name(lot.tender_id) or "_"
                ) / ZIP_FILENAME
                existed = dest.is_file()
                try:
                    status = download_lot_zip(
                        tender_id=lot.tender_id,
                        links=links,
                        platform_id=platform_id,
                        lot_url=lot.url,
                        cookies_path=cookies,
                        docs_root=docs_root,
                        delay_s=delay_s,
                        persist_meta=persist_meta,
                        client=client,
                        should_stop=should_stop,
                    )
                except AuthError:
                    remaining = platform_lots[index:]
                    for rem in remaining:
                        if persist_meta:
                            _set_lot_docs_state(rem.tender_id, status=DOC_STATUS_ERROR)
                        result.errors += 1
                        result.by_status[DOC_STATUS_ERROR] = (
                            result.by_status.get(DOC_STATUS_ERROR, 0) + 1
                        )
                    break
                except Exception:  # noqa: BLE001
                    status = DOC_STATUS_ERROR
                    if persist_meta:
                        _set_lot_docs_state(lot.tender_id, status=DOC_STATUS_ERROR)
                    result.errors += 1
                    result.by_status[status] = result.by_status.get(status, 0) + 1
                    continue

                result.by_status[status] = result.by_status.get(status, 0) + 1
                if status == DOC_STATUS_READY:
                    if existed:
                        result.skipped += 1
                    else:
                        result.saved += 1
                elif status == DOC_STATUS_ERROR:
                    result.errors += 1

    return result


def download_inbox_docs(
    rows: list[dict],
    *,
    cookies_path: Path,
    docs_root: Path | None = None,
    delay_s: float = 0.2,
    should_stop=None,
    persist_meta: bool = True,
    client: httpx.Client | None = None,
) -> DocsPassResult:
    """Legacy entry: zip from in-memory rows (cli). Prefer run_docs_pass after AI."""
    if not download_docs_enabled():
        return DocsPassResult()
    result = DocsPassResult()
    seen: set[str] = set()
    for row in rows:
        if should_stop and should_stop():
            break
        tier = str(row.get("tier") or "").strip()
        if tier not in INBOX_TIERS:
            continue
        tender_id = str(row.get("tender_id") or "").strip()
        if not tender_id or tender_id in seen:
            continue
        seen.add(tender_id)
        platform, _ = split_tender_id(tender_id)
        platform_id = str(row.get("source_platform_id") or platform or "rostender")
        links = _links_from_raw(row.get("doc_links") or row)
        try:
            status = download_lot_zip(
                tender_id=tender_id,
                links=links,
                platform_id=platform_id,
                lot_url=str(row.get("url") or "") or None,
                cookies_path=cookies_path,
                docs_root=docs_root,
                delay_s=delay_s,
                persist_meta=persist_meta,
                client=client,
                should_stop=should_stop,
            )
        except AuthError:
            raise
        except Exception:  # noqa: BLE001
            status = DOC_STATUS_ERROR
            result.errors += 1
        result.by_status[status] = result.by_status.get(status, 0) + 1
        if status == DOC_STATUS_READY:
            result.saved += 1
        elif status == DOC_STATUS_ERROR:
            result.errors += 1
    return result


def resolve_docs_status_for_api(
    state: LotState | None,
    *,
    ai_reviewed: bool,
) -> str:
    stored = (state.docs_status if state is not None else None) or ""
    stored = stored.strip()
    if stored:
        return stored
    if not ai_reviewed:
        return DOC_STATUS_PENDING_AI
    return DOC_STATUS_PENDING_DOWNLOAD

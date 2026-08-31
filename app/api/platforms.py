"""Platform enable + session status + cookie JSON upload (048 / 055)."""
from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api import notify
from app.api import runner
from app.api.state import STATE
from app.db.models import PlatformSetting
from app.db.session import session_factory
from app.worker.cookies import (
    CookieConvertError,
    json_locor_to_netscape,
    write_netscape_cookies,
)
from app.worker.list_scrape import probe_rostender_cookies
from app.worker import roseltorg as roseltorg_worker
from app.worker import tender_pro as tender_pro_worker
from app.worker.platform_ids import (
    PLATFORM_ROSELTORG,
    PLATFORM_ROSTENDER,
    PLATFORM_TENDER_PRO,
)
from app.worker.search_seeds import PLATFORM_LABELS, PLATFORM_ORDER


class PlatformError(ValueError):
    pass


class PlatformNotFound(LookupError):
    pass


class CookieUploadError(ValueError):
    pass


class PlatformPatch(BaseModel):
    enabled: bool = Field(...)


_COOKIE_PLATFORMS = frozenset({PLATFORM_ROSTENDER, PLATFORM_TENDER_PRO, PLATFORM_ROSELTORG})


def _session_for_platform(platform_id: str, sessions: dict[str, Any], rostender: str) -> str:
    """Map runner session codes → API session vocabulary (no cookie filenames)."""
    if platform_id == "tender-pro":
        return "list_without_login"
    raw = sessions.get(platform_id)
    if platform_id == "rostender":
        raw = raw or rostender
    code = str(raw or "unknown")
    if code == "ok":
        return "ok"
    if code == "expired":
        return "expired"
    if code in {"missing_cookies", "missing"}:
        return "missing"
    return "unknown"


def _api_session_from_probe(probe: str) -> str:
    if probe == "ok":
        return "ok"
    if probe == "expired":
        return "expired"
    return "missing"


def _apply_probe_to_state(platform_id: str, probe: str) -> str:
    api_session = _api_session_from_probe(probe)
    if probe == "missing":
        STATE.set_session("missing_cookies", platform_id=platform_id)
    elif probe == "expired":
        STATE.set_session("expired", platform_id=platform_id)
    else:
        STATE.set_session("ok", platform_id=platform_id)
    return api_session


def _probe_platform(platform_id: str) -> str:
    path = runner._cookies_path(platform_id)
    if platform_id == PLATFORM_ROSTENDER:
        base = os.getenv("ROSTENDER_BASE_URL", "https://rostender.info")
        return probe_rostender_cookies(path, base)
    if platform_id == PLATFORM_TENDER_PRO:
        base = os.getenv("TENDER_PRO_BASE_URL", tender_pro_worker.DEFAULT_BASE)
        return tender_pro_worker.probe_tender_pro_cookies(path, base)
    if platform_id == PLATFORM_ROSELTORG:
        base = os.getenv("ROSELTORG_BASE_URL", roseltorg_worker.DEFAULT_BASE)
        return roseltorg_worker.probe_roseltorg_session(cookies_file=path, base=base)
    return "missing"


def list_platforms() -> dict[str, Any]:
    runner.refresh_session(probe_roseltorg_live=False)
    snap = STATE.snapshot()
    sessions = dict(snap.get("sessions") or {})
    rostender = str(snap.get("session") or "unknown")

    factory = session_factory()
    with factory() as session:
        settings = {
            row.platform_id: bool(row.enabled)
            for row in session.scalars(select(PlatformSetting)).all()
        }

    items = []
    for platform_id in PLATFORM_ORDER:
        items.append(
            {
                "platform_id": platform_id,
                "name": PLATFORM_LABELS.get(platform_id, platform_id),
                "enabled": bool(settings.get(platform_id, False)),
                "session": _session_for_platform(platform_id, sessions, rostender),
            }
        )
    return {"items": items}


def set_platform_enabled(platform_id: str, *, enabled: bool) -> dict[str, Any]:
    slug = platform_id.strip()
    if slug not in PLATFORM_ORDER:
        raise PlatformNotFound("not_found")
    factory = session_factory()
    with factory() as session:
        row = session.get(PlatformSetting, slug)
        if row is None:
            session.add(PlatformSetting(platform_id=slug, enabled=enabled))
        else:
            row.enabled = enabled
        session.commit()
    for item in list_platforms()["items"]:
        if item["platform_id"] == slug:
            return item
    raise PlatformNotFound("not_found")


def upload_platform_cookies(platform_id: str, body: Any) -> dict[str, Any]:
    """LOCOR JSON array → Netscape jar → live probe → optional ops alert."""
    slug = (platform_id or "").strip()
    if slug not in _COOKIE_PLATFORMS:
        raise PlatformNotFound("not_found")

    try:
        netscape = json_locor_to_netscape(body)
    except CookieConvertError as exc:
        raise CookieUploadError(str(exc)) from exc

    path = runner._cookies_path(slug)
    try:
        write_netscape_cookies(path, netscape)
    except OSError as exc:
        raise CookieUploadError("cookies_write_failed") from exc

    probe = _probe_platform(slug)
    api_session = _apply_probe_to_state(slug, probe)
    if api_session in {"expired", "missing"}:
        notify.notify_ops_session(platform_id=slug, session=api_session)

    return {
        "platform_id": slug,
        "session": api_session,
        "probed": True,
    }

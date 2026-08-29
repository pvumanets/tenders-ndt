"""Platform enable + session status (048)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api import runner
from app.api.state import STATE
from app.db.models import PlatformSetting
from app.db.session import session_factory
from app.worker.search_seeds import PLATFORM_LABELS, PLATFORM_ORDER


class PlatformError(ValueError):
    pass


class PlatformNotFound(LookupError):
    pass


class PlatformPatch(BaseModel):
    enabled: bool = Field(...)


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

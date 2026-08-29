"""Enable Tender.Pro / Росэлторг platforms when session cookies are available."""
from __future__ import annotations

import os
from pathlib import Path

from app.db.config import database_url
from app.db.models import PlatformSetting
from app.db.session import session_factory
from app.worker.platform_ids import PLATFORM_ROSELTORG, PLATFORM_TENDER_PRO
from app.worker.roseltorg import cookies_present as roseltorg_cookies_present


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def tender_pro_cookies_present() -> bool:
    raw = os.getenv("TENDER_PRO_COOKIES_FILE", "./cookies.tender-pro.txt")
    path = Path(raw)
    if not path.is_absolute():
        path = _repo_root() / path
    return path.is_file() and path.stat().st_size > 0


def _set_platform_enabled(platform_id: str, want: bool) -> None:
    if not database_url():
        return
    factory = session_factory()
    with factory() as session:
        row = session.get(PlatformSetting, platform_id)
        if row is None:
            session.add(PlatformSetting(platform_id=platform_id, enabled=want))
            session.commit()
            return
        if bool(row.enabled) != want:
            row.enabled = want
            session.commit()


def sync_tender_pro_queue_from_cookies() -> None:
    """Enable Tender.Pro when cookies exist; never auto-disable on boot.

    Operator may enable TP for list-without-login via PUT /api/platforms;
    missing cookie files must not undo that on restart.
    """
    if tender_pro_cookies_present():
        _set_platform_enabled(PLATFORM_TENDER_PRO, True)


def sync_roseltorg_queue_from_credentials() -> None:
    """Enable Росэлторг when Netscape cookies exist; never auto-disable on boot."""
    if roseltorg_cookies_present():
        _set_platform_enabled(PLATFORM_ROSELTORG, True)

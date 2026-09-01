"""Enable Tender.Pro / Росэлторг / B2B-Center platforms when session cookies are available."""
from __future__ import annotations

import os
from pathlib import Path

from app.db.config import database_url
from app.db.models import PlatformSetting
from app.db.session import session_factory
from app.worker.b2b_center import cookies_present as b2b_center_cookies_present
from app.worker import oilb2bcs as oilb2bcs_worker
from app.worker import rts_rosatom as rts_rosatom_worker
from app.worker.platform_ids import (
    PLATFORM_B2B_CENTER,
    PLATFORM_OILB2BCS,
    PLATFORM_ROSELTORG,
    PLATFORM_RTS_ROSATOM,
    PLATFORM_TENDER_PRO,
)
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


def sync_b2b_center_queue_from_cookies() -> None:
    """Enable B2B-Center when Netscape cookies exist; never auto-disable on boot."""
    if b2b_center_cookies_present():
        _set_platform_enabled(PLATFORM_B2B_CENTER, True)


def sync_rts_rosatom_queue_from_cookies() -> None:
    """Enable РТС Росатом when Netscape cookies exist; never auto-disable on boot."""
    if rts_rosatom_worker.cookies_present():
        _set_platform_enabled(PLATFORM_RTS_ROSATOM, True)


def sync_oilb2bcs_queue_from_cookies() -> None:
    """Enable OilB2B when auth cookies exist; never auto-disable on boot."""
    if oilb2bcs_worker.cookies_present():
        _set_platform_enabled(PLATFORM_OILB2BCS, True)

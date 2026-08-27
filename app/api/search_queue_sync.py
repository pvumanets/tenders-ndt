"""Enable Tender.Pro seed packages in queue when cookies file exists (P11)."""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import select

from app.db.config import database_url
from app.db.models import NamedSearch
from app.db.session import session_factory
from app.worker.platform_ids import PLATFORM_TENDER_PRO
from app.worker.search_seeds import search_seed_rows


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def tender_pro_cookies_present() -> bool:
    raw = os.getenv("TENDER_PRO_COOKIES_FILE", "./cookies.tender-pro.txt")
    path = Path(raw)
    if not path.is_absolute():
        path = _repo_root() / path
    return path.is_file() and path.stat().st_size > 0


def sync_tender_pro_queue_from_cookies() -> None:
    """If cookies exist, put Tender.Pro seed packages into the run queue."""
    if not database_url():
        return
    want = tender_pro_cookies_present()
    names = {row["name"] for row in search_seed_rows() if row["platform_id"] == PLATFORM_TENDER_PRO}
    factory = session_factory()
    with factory() as session:
        rows = session.scalars(
            select(NamedSearch).where(
                NamedSearch.platform_id == PLATFORM_TENDER_PRO,
                NamedSearch.name.in_(names),
            )
        ).all()
        changed = False
        for row in rows:
            if bool(row.in_queue) != want:
                row.in_queue = want
                changed = True
        if changed:
            session.commit()

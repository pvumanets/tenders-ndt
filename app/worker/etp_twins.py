"""Cross-ETP twins: prefer Росэлторг over РосТендер for the same procedure number."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Lot, LotState
from app.worker.platform_ids import PLATFORM_ROSELTORG, PLATFORM_ROSTENDER, compose_tender_id

_PROC_ID_RE = re.compile(
    r"\b((?:ATOM|COM|RH|RTST|ROSSETI|KIM(?:-INTERRAO)?|B)\d[\w-]*)\b",
    re.I,
)


def extract_etp_procedure_id(*texts: object) -> str | None:
    for raw in texts:
        if raw is None:
            continue
        if isinstance(raw, dict):
            for key in ("etp_procedure_id", "url", "title", "source_etp"):
                found = extract_etp_procedure_id(raw.get(key))
                if found:
                    return found
            nested = raw.get("raw")
            if isinstance(nested, dict):
                found = extract_etp_procedure_id(nested)
                if found:
                    return found
            continue
        m = _PROC_ID_RE.search(str(raw))
        if m:
            return m.group(1)
    return None


def _hide_lot(session: Session, tender_id: str, *, now: datetime) -> bool:
    state = session.get(LotState, tender_id)
    if state is None:
        session.add(
            LotState(
                tender_id=tender_id,
                board_hidden=True,
                board_hidden_at=now,
            )
        )
        return True
    if state.board_hidden:
        return False
    state.board_hidden = True
    state.board_hidden_at = now
    return True


def _row_matches_native(lot: Lot, native: str) -> bool:
    needle = native.lower()
    raw = lot.raw if isinstance(lot.raw, dict) else {}
    etp = extract_etp_procedure_id(
        raw.get("etp_procedure_id"),
        raw.get("source_etp"),
        lot.url,
        lot.title,
    )
    if etp and etp.lower() == needle:
        return True
    blob = f"{lot.url or ''}\n{lot.title or ''}\n{raw}"
    return needle in blob.lower()


def hide_rostender_twins_for_roseltorg(
    session: Session,
    *,
    native_ids: list[str],
) -> int:
    """Hide rostender lots that reference the same ETP procedure id."""
    now = datetime.now(timezone.utc)
    hidden = 0
    for native in native_ids:
        native = str(native or "").strip()
        if not native:
            continue
        re_tid = compose_tender_id(PLATFORM_ROSELTORG, native)
        if session.get(Lot, re_tid) is None:
            continue
        needle = f"%{native}%"
        twins = list(
            session.scalars(
                select(Lot).where(
                    Lot.source_platform_id == PLATFORM_ROSTENDER,
                    or_(Lot.url.ilike(needle), Lot.title.ilike(needle)),
                )
            ).all()
        )
        # Also scan recent rostender lots' raw for exact etp id (bounded).
        if not twins:
            candidates = list(
                session.scalars(
                    select(Lot)
                    .where(Lot.source_platform_id == PLATFORM_ROSTENDER)
                    .order_by(Lot.ingested_at.desc())
                    .limit(500)
                ).all()
            )
            twins = [lot for lot in candidates if _row_matches_native(lot, native)]
        for lot in twins:
            if not _row_matches_native(lot, native):
                continue
            if _hide_lot(session, lot.tender_id, now=now):
                hidden += 1
    return hidden


def hide_if_roseltorg_exists(
    session: Session,
    *,
    rostender_row: dict[str, Any],
) -> bool:
    """When ingesting rostender, hide it immediately if roseltorg twin already exists."""
    etp = extract_etp_procedure_id(
        rostender_row.get("etp_procedure_id"),
        rostender_row.get("raw") if isinstance(rostender_row.get("raw"), dict) else None,
        rostender_row.get("url"),
        rostender_row.get("title"),
        rostender_row.get("source_etp"),
    )
    if not etp:
        return False
    re_tid = compose_tender_id(PLATFORM_ROSELTORG, etp)
    if session.get(Lot, re_tid) is None:
        return False
    rostender_tid = str(rostender_row.get("tender_id") or "")
    if not rostender_tid.startswith(f"{PLATFORM_ROSTENDER}:"):
        return False
    return _hide_lot(session, rostender_tid, now=datetime.now(timezone.utc))

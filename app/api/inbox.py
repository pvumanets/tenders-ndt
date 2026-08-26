"""P5.4–P5.5: Sales Inbox from Postgres (score ≥ 4). Does not read run JSON."""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import quote

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models import Document, Lot, LotState
from app.db.session import session_factory
from app.worker.docs import resolve_volume_file, sanitize_filename
from app.worker.customer_name import clean_customer_name
from app.worker.ingest import INBOX_MIN_SCORE

TIER_FILTERS = frozenset({"fit", "L1", "L2", "L3"})
PRIORITY_TIERS = frozenset({"L1", "L2", "L3"})
_ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
_DMY_DATE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})")


class InboxQueryError(ValueError):
    """Invalid query or body — map to HTTP 400."""


class InboxNotFound(LookupError):
    """Lot missing from the score ≥ 4 pool — map to HTTP 404."""


def parse_query_date(value: str | None) -> date | None:
    if value is None or value.strip() == "":
        return None
    text = value.strip()
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise InboxQueryError("invalid_date") from exc
    if parsed.isoformat() != text:
        raise InboxQueryError("invalid_date")
    return parsed


def parse_unread(value: str | None) -> bool | None:
    if value is None or value.strip() == "":
        return None
    key = value.strip().lower()
    if key in {"true", "1", "yes"}:
        return True
    if key in {"false", "0", "no"}:
        return False
    raise InboxQueryError("invalid_unread")


def parse_tier_filter(value: str | None) -> str:
    tier = (value or "fit").strip() or "fit"
    if tier not in TIER_FILTERS:
        raise InboxQueryError("invalid_tier")
    return tier


def deadline_date(text: str | None) -> date | None:
    if not text:
        return None
    raw = text.strip()
    iso = _ISO_DATE.match(raw)
    if iso:
        try:
            return date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
        except ValueError:
            return None
    dmy = _DMY_DATE.match(raw)
    if dmy:
        try:
            return date(int(dmy.group(3)), int(dmy.group(2)), int(dmy.group(1)))
        except ValueError:
            return None
    return None


def deadline_iso(text: str | None) -> str | None:
    parsed = deadline_date(text)
    if parsed is not None:
        return parsed.isoformat()
    stripped = (text or "").strip()
    return stripped or None


def ingested_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).date().isoformat()


def parse_viewed_body(body: Any) -> bool:
    if not isinstance(body, dict) or "viewed" not in body:
        raise InboxQueryError("invalid_body")
    viewed = body["viewed"]
    if not isinstance(viewed, bool):
        raise InboxQueryError("invalid_body")
    return viewed


def parse_priority_body(body: Any) -> str | None:
    if not isinstance(body, dict) or "tier" not in body:
        raise InboxQueryError("invalid_body")
    if len(body) != 1:
        extra = set(body) - {"tier"}
        if extra:
            raise InboxQueryError("invalid_body")
    tier = body["tier"]
    if tier is None:
        return None
    if not isinstance(tier, str) or tier not in PRIORITY_TIERS:
        raise InboxQueryError("invalid_tier")
    return tier


def _price_json(value: Decimal | None) -> int | float | None:
    if value is None:
        return None
    quantized = value.quantize(Decimal("0.01"))
    as_int = int(quantized)
    if Decimal(as_int) == quantized:
        return as_int
    return float(quantized)


def _effective_tier(lot: Lot, state: LotState | None) -> str:
    if state is not None and state.manual_tier:
        return state.manual_tier
    return lot.tier


def _in_date_range(value: date | None, start: date | None, end: date | None) -> bool:
    if start is None and end is None:
        return True
    if value is None:
        return False
    if start is not None and value < start:
        return False
    if end is not None and value > end:
        return False
    return True


def _doc_meta(doc: Document) -> dict[str, Any]:
    return {"name": doc.filename, "size_kb": doc.size_bytes // 1024}


def document_download_url(tender_id: str, filename: str) -> str:
    return f"/api/inbox/{quote(tender_id, safe='')}/documents/{quote(filename, safe='')}"


def _doc_list_item(tender_id: str, doc: Document) -> dict[str, Any]:
    meta = _doc_meta(doc)
    meta["url"] = document_download_url(tender_id, doc.filename)
    return meta


def serialize_lot(
    lot: Lot,
    state: LotState | None,
    *,
    documents: list[Document] | None = None,
    include_documents: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "tender_id": lot.tender_id,
        "title": lot.title,
        "customer_name": clean_customer_name(lot.customer_name),
        "score": lot.score,
        "tier": lot.tier,
        "effective_tier": _effective_tier(lot, state),
        "manual_tier": state.manual_tier if state is not None else None,
        "viewed": bool(state.viewed) if state is not None else False,
        "deadline_msk": deadline_iso(lot.deadline_msk),
        "ingested_at": ingested_iso(lot.ingested_at),
        "price_rub": _price_json(lot.price_rub),
        "fit_reason": lot.fit_reason,
        "location": lot.location,
        "status": lot.status,
        "url": lot.url,
        "source_platform_id": lot.source_platform_id,
        "contact_name": lot.contact_name,
        "contact_phone": lot.contact_phone,
        "contact_email": lot.contact_email,
    }
    if include_documents:
        rows = documents if documents is not None else []
        payload["documents"] = [_doc_meta(row) for row in rows]
    return payload


def _sort_key(lot: Lot) -> tuple[int, date, str]:
    due = deadline_date(lot.deadline_msk) or date.max
    return (-lot.score, due, lot.tender_id)


def list_inbox(
    *,
    unread: str | None = None,
    tier: str | None = None,
    q: str = "",
    deadline_from: str | None = None,
    deadline_to: str | None = None,
    ingested_from: str | None = None,
    ingested_to: str | None = None,
) -> dict[str, Any]:
    unread_flag = parse_unread(unread)
    tier_filter = parse_tier_filter(tier)
    dl_from = parse_query_date(deadline_from)
    dl_to = parse_query_date(deadline_to)
    ing_from = parse_query_date(ingested_from)
    ing_to = parse_query_date(ingested_to)
    needle = (q or "").strip()

    factory = session_factory()
    with factory() as session:
        stmt = (
            select(Lot, LotState)
            .outerjoin(LotState, LotState.tender_id == Lot.tender_id)
            .where(Lot.score >= INBOX_MIN_SCORE)
        )
        if unread_flag is True:
            stmt = stmt.where(or_(LotState.viewed.is_(None), LotState.viewed.is_(False)))
        if needle:
            pattern = f"%{needle}%"
            stmt = stmt.where(
                or_(
                    Lot.title.ilike(pattern),
                    Lot.customer_name.ilike(pattern),
                    Lot.tender_id.ilike(pattern),
                    Lot.location.ilike(pattern),
                )
            )
        rows = list(session.execute(stmt).all())
        filtered: list[tuple[Lot, LotState | None]] = []
        for lot, state in rows:
            if tier_filter != "fit" and _effective_tier(lot, state) != tier_filter:
                continue
            if not _in_date_range(deadline_date(lot.deadline_msk), dl_from, dl_to):
                continue
            ingested = None
            if lot.ingested_at is not None:
                stamp = lot.ingested_at
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=timezone.utc)
                ingested = stamp.astimezone(timezone.utc).date()
            if not _in_date_range(ingested, ing_from, ing_to):
                continue
            filtered.append((lot, state))
        filtered.sort(key=lambda pair: _sort_key(pair[0]))
        items = [serialize_lot(lot, state) for lot, state in filtered]
        return {"items": items, "total": len(items)}


def _require_pool_lot(session, tender_id: str) -> Lot:
    lot = session.get(Lot, tender_id)
    if lot is None or lot.score < INBOX_MIN_SCORE:
        raise InboxNotFound(tender_id)
    return lot


def get_inbox_item(tender_id: str) -> dict[str, Any]:
    factory = session_factory()
    with factory() as session:
        lot = _require_pool_lot(session, tender_id)
        state = session.get(LotState, tender_id)
        docs = list(
            session.scalars(select(Document).where(Document.tender_id == tender_id)).all()
        )
        return serialize_lot(lot, state, documents=docs, include_documents=True)


def set_viewed(tender_id: str, body: Any) -> dict[str, Any]:
    viewed = parse_viewed_body(body)
    now = datetime.now(timezone.utc)
    factory = session_factory()
    with factory() as session:
        _require_pool_lot(session, tender_id)
        values: dict[str, Any] = {"tender_id": tender_id, "viewed": viewed}
        if viewed:
            values["viewed_at"] = now
        stmt = pg_insert(LotState).values(values)
        update = {"viewed": viewed}
        if viewed:
            update["viewed_at"] = now
        session.execute(stmt.on_conflict_do_update(index_elements=["tender_id"], set_=update))
        session.commit()
        lot = session.get(Lot, tender_id)
        state = session.get(LotState, tender_id)
        docs = list(
            session.scalars(select(Document).where(Document.tender_id == tender_id)).all()
        )
        assert lot is not None
        return serialize_lot(lot, state, documents=docs, include_documents=True)


def set_priority(tender_id: str, body: Any) -> dict[str, Any]:
    tier = parse_priority_body(body)
    now = datetime.now(timezone.utc)
    factory = session_factory()
    with factory() as session:
        _require_pool_lot(session, tender_id)
        stmt = pg_insert(LotState).values(
            tender_id=tender_id,
            manual_tier=tier,
            manual_tier_at=now,
        )
        session.execute(
            stmt.on_conflict_do_update(
                index_elements=["tender_id"],
                set_={"manual_tier": tier, "manual_tier_at": now},
            )
        )
        session.commit()
        lot = session.get(Lot, tender_id)
        state = session.get(LotState, tender_id)
        docs = list(
            session.scalars(select(Document).where(Document.tender_id == tender_id)).all()
        )
        assert lot is not None
        return serialize_lot(lot, state, documents=docs, include_documents=True)


def list_documents(tender_id: str) -> dict[str, Any]:
    factory = session_factory()
    with factory() as session:
        _require_pool_lot(session, tender_id)
        docs = list(
            session.scalars(
                select(Document)
                .where(Document.tender_id == tender_id)
                .order_by(Document.filename)
            ).all()
        )
        return {"items": [_doc_list_item(tender_id, row) for row in docs]}


def download_document(tender_id: str, filename: str) -> Path:
    safe = sanitize_filename(filename)
    if safe is None or safe != filename:
        raise InboxQueryError("invalid_filename")
    factory = session_factory()
    with factory() as session:
        _require_pool_lot(session, tender_id)
        doc = session.scalar(
            select(Document).where(
                Document.tender_id == tender_id,
                Document.filename == filename,
            )
        )
        if doc is None:
            raise InboxNotFound(filename)
    path = resolve_volume_file(tender_id, filename)
    if path is None:
        raise InboxNotFound(filename)
    return path

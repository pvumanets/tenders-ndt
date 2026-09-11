"""P5.4–P5.5 + P8–P10: Sales Inbox from Postgres (tier L1–L3). Does not read run JSON."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.api.operator_settings import read_ai_system_prompt, read_l1_min_price_rub
from app.deadline import deadline_date, deadline_iso, is_deadline_expired, today_msk_date
from app.db.models import Document, Lot, LotState, TierTeachEvent
from app.db.session import session_factory
from app.worker.ingest import INBOX_TIERS
from app.worker.customer_name import clean_customer_name
from app.worker.docs import resolve_volume_file, sanitize_filename

TIER_FILTERS = frozenset({"fit", "L1", "L2", "L3"})
PRIORITY_TIERS = frozenset({"L1", "L2", "L3"})
TEACH_BUCKETS = frozenset({"L1", "L2", "L3", "expired"})
INBOX_SORTS = frozenset({"relevance", "appeared", "deadline"})
DEFAULT_INBOX_SORT = "relevance"
AI_REVIEW_CAP = 100
TEACH_REASON_MAX = 2000
TEACH_LIST_DEFAULT = 100
TEACH_LIST_MAX = 500


class InboxQueryError(ValueError):
    """Invalid query or body — map to HTTP 400."""


class InboxNotFound(LookupError):
    """Lot missing from the L1–L3 pool — map to HTTP 404."""


class InboxConflict(RuntimeError):
    """HTTP 409 — e.g. already_sent to Bitrix."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


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


def parse_inbox_sort(value: str | None) -> str:
    """Unknown/empty → relevance (no 400)."""
    key = (value or "").strip().lower()
    if key in INBOX_SORTS:
        return key
    return DEFAULT_INBOX_SORT


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


def parse_board_hidden_body(body: Any) -> bool:
    if not isinstance(body, dict) or "hidden" not in body:
        raise InboxQueryError("invalid_body")
    hidden = body["hidden"]
    if not isinstance(hidden, bool):
        raise InboxQueryError("invalid_body")
    return hidden


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


def parse_ai_reviewed(value: str | None) -> bool | None:
    if value is None or value.strip() == "":
        return None
    key = value.strip().lower()
    if key in {"true", "1", "yes"}:
        return True
    if key in {"false", "0", "no"}:
        return False
    raise InboxQueryError("invalid_ai_reviewed")


def parse_ai_trigger(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    key = value.strip().lower()
    if key in {"auto", "manual"}:
        return key
    raise InboxQueryError("invalid_ai_trigger")


def parse_price_min_rub(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    text = value.strip()
    try:
        parsed = int(text)
    except ValueError as exc:
        raise InboxQueryError("invalid_price_min_rub") from exc
    if parsed < 0:
        raise InboxQueryError("invalid_price_min_rub")
    if parsed == 0:
        return None
    return parsed


def parse_platform_filter(value: str | None) -> frozenset[str] | None:
    if value is None or value.strip() == "":
        return None
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts:
        return None
    return frozenset(parts)


def parse_bitrix_filter(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    key = value.strip().lower()
    if key in {"in", "out"}:
        return key
    raise InboxQueryError("invalid_bitrix")


def parse_ai_wrong(value: str | bool | None) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = value.strip()
    if text == "":
        return None
    key = text.lower()
    if key in {"true", "1", "yes"}:
        return True
    if key in {"false", "0", "no"}:
        return False
    raise InboxQueryError("invalid_ai_wrong")


def parse_ai_error(value: str | bool | None) -> bool | None:
    """Filter lots with non-empty lot_state.ai_error (ИИ сбой)."""
    try:
        return parse_ai_wrong(value)
    except InboxQueryError as exc:
        raise InboxQueryError("invalid_ai_error") from exc


def _price_below_min(lot: Lot, min_price: int | None) -> bool:
    if min_price is None:
        return False
    if lot.price_rub is None:
        return False
    return lot.price_rub < min_price


def _base_tier(lot: Lot, state: LotState | None) -> str:
    if state is not None and state.manual_tier:
        return state.manual_tier
    if state is not None and state.ai_reviewed_at is not None and state.ai_tier in PRIORITY_TIERS:
        return state.ai_tier
    return lot.tier


def _effective_tier(lot: Lot, state: LotState | None, *, min_price: int | None = None) -> str:
    if state is not None and state.manual_tier == "L1":
        return "L1"
    base = _base_tier(lot, state)
    if (
        base == "L1"
        and min_price is not None
        and lot.price_rub is not None
        and lot.price_rub < min_price
    ):
        return "L2"
    return base


def lot_eligible_for_auto_ai(
    *,
    tier: str,
    deadline_msk: str | None,
    board_hidden: bool,
    ai_reviewed_at: datetime | None,
) -> bool:
    if tier not in INBOX_TIERS:
        return False
    if board_hidden:
        return False
    if ai_reviewed_at is not None:
        return False
    if is_deadline_expired(deadline_msk):
        return False
    return True


def select_auto_ai_ids(
    candidates: list[dict[str, Any]],
    *,
    prefer_ids: set[str],
) -> list[str]:
    """Prefer ∩ eligible. Empty prefer after a successful auto queue → no-op."""
    if not prefer_ids:
        return []
    out: list[str] = []
    for row in candidates:
        tid = str(row.get("tender_id") or "").strip()
        if tid not in prefer_ids:
            continue
        if lot_eligible_for_auto_ai(
            tier=str(row.get("tier") or ""),
            deadline_msk=row.get("deadline_msk") if isinstance(row.get("deadline_msk"), str) else None,
            board_hidden=bool(row.get("board_hidden")),
            ai_reviewed_at=row.get("ai_reviewed_at")
            if isinstance(row.get("ai_reviewed_at"), datetime)
            else None,
        ):
            out.append(tid)
    return out


def _in_pool(lot: Lot) -> bool:
    if lot.tier not in INBOX_TIERS:
        return False
    # Align with list_inbox: undated lots are not on the operator surface.
    return deadline_date(lot.deadline_msk) is not None


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
    today: date | None = None,
    min_price: int | None = None,
) -> dict[str, Any]:
    due = deadline_date(lot.deadline_msk)
    today_d = today_msk_date(today)
    expired = due is not None and due < today_d
    ai_reviewed = bool(state is not None and state.ai_reviewed_at is not None)
    from app.worker.docs import resolve_docs_status_for_api

    docs_status = resolve_docs_status_for_api(state, ai_reviewed=ai_reviewed)
    payload: dict[str, Any] = {
        "tender_id": lot.tender_id,
        "title": lot.title,
        "customer_name": clean_customer_name(lot.customer_name),
        "score": lot.score,
        "tier": lot.tier,
        "effective_tier": _effective_tier(lot, state, min_price=min_price),
        "manual_tier": state.manual_tier if state is not None else None,
        "viewed": bool(state.viewed) if state is not None else False,
        "board_hidden": bool(state.board_hidden) if state is not None else False,
        "deadline_expired": expired,
        "deadline_msk": deadline_iso(lot.deadline_msk),
        "published_msk": deadline_iso(lot.published_msk),
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
        "rules_tier": (state.rules_tier if state is not None else None) or lot.tier,
        "ai_reviewed": ai_reviewed,
        "ai_reviewed_at": ingested_iso(state.ai_reviewed_at) if state is not None else None,
        "ai_tier": state.ai_tier if state is not None else None,
        "ai_reason_ru": state.ai_reason_ru if state is not None else None,
        "ai_error": state.ai_error if state is not None else None,
        "ai_wrong": bool(state is not None and state.ai_wrong_at is not None),
        "ai_wrong_note": (state.ai_wrong_note if state is not None else None) or None,
        "ai_trigger": state.ai_trigger if state is not None else None,
        "bitrix_sent_at": ingested_iso(state.bitrix_sent_at)
        if state is not None and state.bitrix_sent_at is not None
        else None,
        "customer_inn": lot.customer_inn,
        "docs_status": docs_status,
        "docs_external_url": (state.docs_external_url if state is not None else None),
    }
    if include_documents:
        rows = documents if documents is not None else []
        # TO-BE: one zip only
        zip_rows = [row for row in rows if row.filename.lower().endswith(".zip")]
        show = zip_rows[:1] if zip_rows else []
        payload["documents"] = [_doc_meta(row) for row in show]
        payload["documents_count"] = len(show)
    return payload


def _ingested_stamp(lot: Lot) -> datetime:
    stamp = lot.ingested_at
    if stamp is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if stamp.tzinfo is None:
        return stamp.replace(tzinfo=timezone.utc)
    return stamp


def _sort_key_live(lot: Lot, *, sort: str) -> tuple:
    due = deadline_date(lot.deadline_msk) or date.max
    if sort == "appeared":
        return (-_ingested_stamp(lot).timestamp(), lot.tender_id)
    if sort == "deadline":
        return (due, -lot.score, lot.tender_id)
    # relevance (default)
    return (-lot.score, due, lot.tender_id)


def _sort_key_expired(lot: Lot, *, sort: str) -> tuple:
    """Freshest expired first by default; appeared uses first-seen DESC."""
    due = deadline_date(lot.deadline_msk) or date.min
    if sort == "appeared":
        return (_ingested_stamp(lot), lot.tender_id)
    return (due, lot.tender_id)


def list_inbox(
    *,
    unread: str | None = None,
    tier: str | None = None,
    q: str = "",
    deadline_from: str | None = None,
    deadline_to: str | None = None,
    ingested_from: str | None = None,
    ingested_to: str | None = None,
    ai_reviewed: str | None = None,
    ai_trigger: str | None = None,
    ai_wrong: str | bool | None = None,
    ai_error: str | bool | None = None,
    price_min_rub: str | None = None,
    platform: str | None = None,
    bitrix: str | None = None,
    sort: str | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    unread_flag = parse_unread(unread)
    tier_filter = parse_tier_filter(tier)
    sort_mode = parse_inbox_sort(sort)
    ai_flag = parse_ai_reviewed(ai_reviewed)
    trigger = parse_ai_trigger(ai_trigger)
    ai_wrong_flag = parse_ai_wrong(ai_wrong)
    ai_error_flag = parse_ai_error(ai_error)
    price_min = parse_price_min_rub(price_min_rub)
    platform_ids = parse_platform_filter(platform)
    bitrix_filter = parse_bitrix_filter(bitrix)
    dl_from = parse_query_date(deadline_from)
    dl_to = parse_query_date(deadline_to)
    ing_from = parse_query_date(ingested_from)
    ing_to = parse_query_date(ingested_to)
    needle = (q or "").strip()
    today_d = today_msk_date(today)

    factory = session_factory()
    with factory() as session:
        l1_min_price = read_l1_min_price_rub(session)
        stmt = (
            select(Lot, LotState)
            .outerjoin(LotState, LotState.tender_id == Lot.tender_id)
            .where(Lot.tier.in_(tuple(INBOX_TIERS)))
        )
        if unread_flag is True:
            stmt = stmt.where(or_(LotState.viewed.is_(None), LotState.viewed.is_(False)))
        if ai_flag is True:
            stmt = stmt.where(LotState.ai_reviewed_at.is_not(None))
        if ai_flag is False:
            stmt = stmt.where(
                or_(LotState.ai_reviewed_at.is_(None), LotState.tender_id.is_(None))
            )
        if trigger is not None:
            stmt = stmt.where(LotState.ai_trigger == trigger)
        if ai_wrong_flag is True:
            stmt = stmt.where(LotState.ai_wrong_at.is_not(None))
        elif ai_wrong_flag is False:
            stmt = stmt.where(
                or_(LotState.ai_wrong_at.is_(None), LotState.tender_id.is_(None))
            )
        if ai_error_flag is True:
            stmt = stmt.where(
                LotState.ai_error.is_not(None),
                LotState.ai_error != "",
            )
        elif ai_error_flag is False:
            stmt = stmt.where(
                or_(LotState.ai_error.is_(None), LotState.ai_error == "", LotState.tender_id.is_(None))
            )
        if platform_ids is not None:
            stmt = stmt.where(Lot.source_platform_id.in_(tuple(platform_ids)))
        if bitrix_filter == "in":
            stmt = stmt.where(LotState.bitrix_sent_at.is_not(None))
        elif bitrix_filter == "out":
            stmt = stmt.where(or_(LotState.bitrix_sent_at.is_(None), LotState.tender_id.is_(None)))
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
        live: list[tuple[Lot, LotState | None]] = []
        expired: list[tuple[Lot, LotState | None]] = []
        for lot, state in rows:
            if state is not None and state.board_hidden:
                continue
            if _price_below_min(lot, price_min):
                continue
            due = deadline_date(lot.deadline_msk)
            if due is None:
                continue
            if tier_filter != "fit" and _effective_tier(lot, state, min_price=l1_min_price) != tier_filter:
                continue
            if not _in_date_range(due, dl_from, dl_to):
                continue
            ingested = None
            if lot.ingested_at is not None:
                stamp = lot.ingested_at
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=timezone.utc)
                ingested = stamp.astimezone(timezone.utc).date()
            if not _in_date_range(ingested, ing_from, ing_to):
                continue
            if due < today_d:
                expired.append((lot, state))
            else:
                live.append((lot, state))
        live.sort(key=lambda pair: _sort_key_live(pair[0], sort=sort_mode))
        expired.sort(
            key=lambda pair: _sort_key_expired(pair[0], sort=sort_mode),
            reverse=True,
        )
        filtered = live + expired
        items = [
            serialize_lot(lot, state, today=today_d, min_price=l1_min_price)
            for lot, state in filtered
        ]
        return {"items": items, "total": len(items)}


def _require_pool_lot(session, tender_id: str) -> Lot:
    lot = session.get(Lot, tender_id)
    if lot is None or not _in_pool(lot):
        raise InboxNotFound(tender_id)
    return lot


def get_inbox_item(tender_id: str) -> dict[str, Any]:
    factory = session_factory()
    with factory() as session:
        min_price = read_l1_min_price_rub(session)
        lot = _require_pool_lot(session, tender_id)
        state = session.get(LotState, tender_id)
        docs = list(
            session.scalars(select(Document).where(Document.tender_id == tender_id)).all()
        )
        return serialize_lot(
            lot, state, documents=docs, include_documents=True, min_price=min_price
        )


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
        min_price = read_l1_min_price_rub(session)
        docs = list(
            session.scalars(select(Document).where(Document.tender_id == tender_id)).all()
        )
        assert lot is not None
        return serialize_lot(
            lot, state, documents=docs, include_documents=True, min_price=min_price
        )


def parse_mark_all_viewed_body(body: Any) -> tuple[bool | None, str | None, bool]:
    """Return (ai_reviewed_flag, ai_trigger, dry_run). Tab scope only."""
    if body is None:
        body = {}
    if not isinstance(body, dict):
        raise InboxQueryError("invalid_body")
    dry_run = bool(body.get("dry_run"))
    ai_raw = body.get("ai_reviewed")
    ai_flag: bool | None
    if ai_raw is None:
        ai_flag = None
    elif isinstance(ai_raw, bool):
        ai_flag = ai_raw
    elif ai_raw in (1, "1", "true", "True"):
        ai_flag = True
    elif ai_raw in (0, "0", "false", "False"):
        ai_flag = False
    else:
        raise InboxQueryError("invalid_ai_reviewed")
    trigger_raw = body.get("ai_trigger")
    trigger: str | None
    if trigger_raw is None or trigger_raw == "":
        trigger = None
    else:
        trigger = parse_ai_trigger(str(trigger_raw))
    return ai_flag, trigger, dry_run


def _unread_tab_tender_ids(
    session,
    *,
    ai_flag: bool | None,
    trigger: str | None,
) -> list[str]:
    """Unread lots on a tab (ignore UI filters). Matches list_inbox unread + AI scope + not hidden."""
    stmt = (
        select(Lot, LotState)
        .outerjoin(LotState, LotState.tender_id == Lot.tender_id)
        .where(Lot.tier.in_(tuple(INBOX_TIERS)))
        .where(or_(LotState.viewed.is_(None), LotState.viewed.is_(False)))
    )
    if ai_flag is True:
        stmt = stmt.where(LotState.ai_reviewed_at.is_not(None))
    elif ai_flag is False:
        stmt = stmt.where(
            or_(LotState.ai_reviewed_at.is_(None), LotState.tender_id.is_(None))
        )
    if trigger is not None:
        stmt = stmt.where(LotState.ai_trigger == trigger)
    ids: list[str] = []
    for lot, state in session.execute(stmt).all():
        if state is not None and state.board_hidden:
            continue
        if deadline_date(lot.deadline_msk) is None:
            continue
        ids.append(lot.tender_id)
    return ids


def mark_all_viewed(body: Any = None) -> dict[str, Any]:
    """Mark all unread lots in the current tab scope as viewed. Optional dry_run → count only."""
    ai_flag, trigger, dry_run = parse_mark_all_viewed_body(body)
    now = datetime.now(timezone.utc)
    factory = session_factory()
    with factory() as session:
        ids = _unread_tab_tender_ids(session, ai_flag=ai_flag, trigger=trigger)
        if dry_run:
            return {"count": len(ids), "updated": 0}
        for tender_id in ids:
            values: dict[str, Any] = {
                "tender_id": tender_id,
                "viewed": True,
                "viewed_at": now,
            }
            stmt = pg_insert(LotState).values(values)
            session.execute(
                stmt.on_conflict_do_update(
                    index_elements=["tender_id"],
                    set_={"viewed": True, "viewed_at": now},
                )
            )
        session.commit()
        return {"count": len(ids), "updated": len(ids)}


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
        min_price = read_l1_min_price_rub(session)
        docs = list(
            session.scalars(select(Document).where(Document.tender_id == tender_id)).all()
        )
        assert lot is not None
        return serialize_lot(
            lot, state, documents=docs, include_documents=True, min_price=min_price
        )


def set_board_hidden(tender_id: str, body: Any) -> dict[str, Any]:
    hidden = parse_board_hidden_body(body)
    now = datetime.now(timezone.utc)
    factory = session_factory()
    with factory() as session:
        _require_pool_lot(session, tender_id)
        values: dict[str, Any] = {
            "tender_id": tender_id,
            "board_hidden": hidden,
            "board_hidden_at": now if hidden else None,
        }
        stmt = pg_insert(LotState).values(values)
        session.execute(
            stmt.on_conflict_do_update(
                index_elements=["tender_id"],
                set_={
                    "board_hidden": hidden,
                    "board_hidden_at": now if hidden else None,
                },
            )
        )
        session.commit()
        lot = session.get(Lot, tender_id)
        state = session.get(LotState, tender_id)
        min_price = read_l1_min_price_rub(session)
        docs = list(
            session.scalars(select(Document).where(Document.tender_id == tender_id)).all()
        )
        assert lot is not None
        return serialize_lot(
            lot, state, documents=docs, include_documents=True, min_price=min_price
        )


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


def _ensure_lot_state(session, tender_id: str) -> LotState:
    state = session.get(LotState, tender_id)
    if state is not None:
        return state
    state = LotState(tender_id=tender_id)
    session.add(state)
    session.flush()
    return state


def _lot_description(lot: Lot) -> str | None:
    """Optional purchase description from lot.raw (no dedicated column)."""
    raw = lot.raw
    if not isinstance(raw, dict):
        return None
    desc = raw.get("description")
    if not isinstance(desc, str):
        return None
    text = desc.strip()
    return text or None


def _apply_ai_review(
    pairs: list[tuple[Lot, LotState | None]],
    *,
    trigger: str,
    skip_hidden_expired: bool = True,
) -> dict[str, Any]:
    from app.ai.provod import AiTierError, is_host_transient_error, review_tier
    from app.api.state import STATE

    factory = session_factory()
    processed = 0
    failed = 0
    items: list[dict[str, Any]] = []
    l1_ids: list[str] = []
    work = list(pairs)
    consecutive_host_fails = 0
    circuit_broken = False
    host_fail_limit = 3
    STATE.set_ai_progress(0, len(work))
    with factory() as session:
        min_price = read_l1_min_price_rub(session)
        system_prompt = read_ai_system_prompt(session)
        for index, (lot, state) in enumerate(work):
            if circuit_broken:
                break
            if skip_hidden_expired:
                if state is not None and state.board_hidden:
                    STATE.set_ai_progress(index + 1, len(work))
                    continue
                if is_deadline_expired(lot.deadline_msk):
                    STATE.set_ai_progress(index + 1, len(work))
                    continue
            now = datetime.now(timezone.utc)
            lot = session.get(Lot, lot.tender_id)
            if lot is None:
                STATE.set_ai_progress(index + 1, len(work))
                continue
            state = _ensure_lot_state(session, lot.tender_id)
            if not state.rules_tier:
                state.rules_tier = lot.tier
            try:
                result = review_tier(
                    title=lot.title,
                    customer_name=clean_customer_name(lot.customer_name),
                    description=_lot_description(lot),
                    system_prompt=system_prompt,
                )
                state.ai_tier = result.tier
                state.ai_reason_ru = result.reason_ru
                state.ai_reviewed_at = now
                state.ai_error = None
                state.ai_trigger = trigger
                processed += 1
                consecutive_host_fails = 0
                if result.tier == "L1":
                    l1_ids.append(lot.tender_id)
            except AiTierError as exc:
                state.ai_error = str(exc.message)
                failed += 1
                if is_host_transient_error(exc.message):
                    consecutive_host_fails += 1
                    if consecutive_host_fails >= host_fail_limit:
                        circuit_broken = True
                        STATE.log_msg(
                            f"ИИ: circuit-break после {consecutive_host_fails} host-сбоев подряд",
                            level="warn",
                        )
                else:
                    consecutive_host_fails = 0
            except Exception as exc:
                state.ai_error = str(exc)[:240]
                failed += 1
                consecutive_host_fails = 0
            session.flush()
            session.commit()
            docs = list(
                session.scalars(select(Document).where(Document.tender_id == lot.tender_id)).all()
            )
            items.append(
                serialize_lot(
                    lot, state, documents=docs, include_documents=True, min_price=min_price
                )
            )
            STATE.set_ai_progress(index + 1, len(work))

    STATE.set_ai_failures(failed)
    if failed:
        STATE.log_msg(f"ИИ: сбоев {failed}, успешно {processed}", level="warn")
        from app.api.notify import notify_ops_event

        notify_ops_event(
            subject="сбой ИИ",
            body=f"Успешно: {processed}\nСбоев: {failed}"
            + ("\nCircuit-break: да" if circuit_broken else ""),
        )
    else:
        STATE.log_msg(f"ИИ: разобрано {processed}")
    leads_sent = 0
    if l1_ids:
        from app.bitrix.auto_leads import notify_auto_l1_leads

        counts = notify_auto_l1_leads(l1_ids)
        leads_sent = int(counts.get("sent") or 0)
    docs_ids = [lot.tender_id for lot, _state in work if lot.tier in INBOX_TIERS]
    docs_report = _run_docs_pass_after_ai(docs_ids)
    return {
        "processed": processed,
        "failed": failed,
        "items": items,
        "leads_sent": leads_sent,
        "l1_candidate_n": len(l1_ids),
        "docs": docs_report,
        "circuit_broken": circuit_broken,
    }


def _run_docs_pass_after_ai(tender_ids: list[str]) -> dict[str, Any]:
    """094: zip docs-pass after AI batch (manual or auto)."""
    from app.api.state import STATE
    from app.worker.docs import download_docs_enabled, run_docs_pass

    if not tender_ids:
        return {"saved": 0, "skipped": 0, "errors": 0}
    if not download_docs_enabled():
        STATE.log_msg("Docs: skip (DOWNLOAD_DOCS=0)")
        return {"saved": 0, "skipped": 0, "errors": 0, "skipped_flag": True}
    STATE.log_msg(f"Docs: after AI — {len(tender_ids)} lot(s)…")
    try:
        result = run_docs_pass(tender_ids, should_stop=STATE.should_stop)
        STATE.log_msg(
            f"Docs: saved={result.saved} skipped={result.skipped} errors={result.errors}"
        )
        return {
            "saved": result.saved,
            "skipped": result.skipped,
            "errors": result.errors,
            "by_status": dict(result.by_status),
        }
    except Exception as exc:  # noqa: BLE001
        STATE.log_msg(f"Docs error: {type(exc).__name__}: {exc}", level="error")
        return {"saved": 0, "skipped": 0, "errors": 1, "error": type(exc).__name__}


def run_ai_review(body: Any) -> dict[str, Any]:
    """POST /api/inbox/ai-review — operator-triggered; never called from runner."""
    ids: list[str] | None = None
    retry_errors = False
    if body is None or body == {}:
        ids = None
    elif isinstance(body, dict):
        retry_errors = bool(body.get("retry_errors"))
        raw_ids = body.get("tender_ids")
        if raw_ids is None:
            ids = None
        elif isinstance(raw_ids, list) and all(isinstance(x, str) for x in raw_ids):
            ids = [x.strip() for x in raw_ids if str(x).strip()]
        else:
            raise InboxQueryError("invalid_body")
    else:
        raise InboxQueryError("invalid_body")

    factory = session_factory()
    failed_missing = 0
    with factory() as session:
        if ids is None:
            stmt = (
                select(Lot, LotState)
                .outerjoin(LotState, LotState.tender_id == Lot.tender_id)
                .where(Lot.tier.in_(tuple(INBOX_TIERS)))
                .where(or_(LotState.ai_reviewed_at.is_(None), LotState.tender_id.is_(None)))
            )
            if retry_errors:
                stmt = stmt.where(
                    LotState.ai_error.is_not(None),
                    LotState.ai_error != "",
                )
            pairs = list(session.execute(stmt).all())
        else:
            pairs = []
            for tid in ids:
                lot = session.get(Lot, tid)
                if lot is None or not _in_pool(lot):
                    failed_missing += 1
                    continue
                pairs.append((lot, session.get(LotState, tid)))

    pairs = pairs[:AI_REVIEW_CAP]
    result = _apply_ai_review(pairs, trigger="manual")
    result["failed"] = int(result.get("failed") or 0) + failed_missing
    return result


def run_auto_ai_review(prefer_ids: set[str], *, trigger: str = "auto") -> dict[str, Any]:
    """After scrape queue: prefer ∩ eligible. Empty prefer → no-op. Sets ai_trigger."""
    from app.api.state import STATE

    if trigger not in {"auto", "manual"}:
        trigger = "auto"
    if not prefer_ids:
        STATE.log_msg("Pipeline AI: no-op (empty prefer)")
        return {"processed": 0, "failed": 0, "items": [], "leads_sent": 0}
    factory = session_factory()
    with factory() as session:
        stmt = (
            select(Lot, LotState)
            .outerjoin(LotState, LotState.tender_id == Lot.tender_id)
            .where(Lot.tender_id.in_(tuple(prefer_ids)))
        )
        pairs: list[tuple[Lot, LotState | None]] = []
        for lot, state in session.execute(stmt).all():
            hidden = bool(state.board_hidden) if state is not None else False
            reviewed = state.ai_reviewed_at if state is not None else None
            if lot_eligible_for_auto_ai(
                tier=lot.tier,
                deadline_msk=lot.deadline_msk,
                board_hidden=hidden,
                ai_reviewed_at=reviewed,
            ):
                pairs.append((lot, state))
    if not pairs:
        STATE.log_msg("Pipeline AI: no-op (no eligible lots)")
        return {"processed": 0, "failed": 0, "items": [], "leads_sent": 0}
    pairs = pairs[:AI_REVIEW_CAP]
    return _apply_ai_review(pairs, trigger=trigger, skip_hidden_expired=False)


def mark_ai_wrong(tender_id: str, body: Any) -> dict[str, Any]:
    note: str | None = None
    if body is None or body == {}:
        note = None
    elif isinstance(body, dict):
        raw = body.get("note")
        if raw is None:
            note = None
        elif isinstance(raw, str):
            note = raw.strip() or None
        else:
            raise InboxQueryError("invalid_body")
    else:
        raise InboxQueryError("invalid_body")

    now = datetime.now(timezone.utc)
    factory = session_factory()
    with factory() as session:
        lot = _require_pool_lot(session, tender_id)
        state = _ensure_lot_state(session, tender_id)
        state.ai_wrong_at = now
        state.ai_wrong_note = note
        session.commit()
        min_price = read_l1_min_price_rub(session)
        docs = list(
            session.scalars(select(Document).where(Document.tender_id == tender_id)).all()
        )
        return serialize_lot(
            lot, state, documents=docs, include_documents=True, min_price=min_price
        )


def parse_teach_body(body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise InboxQueryError("invalid_body")
    from_bucket = body.get("from_bucket")
    to_bucket = body.get("to_bucket")
    if from_bucket not in TEACH_BUCKETS or to_bucket not in TEACH_BUCKETS:
        raise InboxQueryError("invalid_bucket")
    if from_bucket == to_bucket:
        raise InboxQueryError("same_bucket")
    correct = body.get("drop_tier_correct")
    if not isinstance(correct, bool):
        raise InboxQueryError("invalid_drop_tier_correct")
    reason_raw = body.get("reason_ru")
    if not isinstance(reason_raw, str):
        raise InboxQueryError("invalid_reason")
    reason = reason_raw.strip()
    if not reason or len(reason) > TEACH_REASON_MAX:
        raise InboxQueryError("invalid_reason")
    return {
        "from_bucket": from_bucket,
        "to_bucket": to_bucket,
        "drop_tier_correct": correct,
        "reason_ru": reason,
    }


def record_tier_teach(
    tender_id: str,
    body: Any,
    *,
    user_id: UUID | None = None,
) -> dict[str, Any]:
    parsed = parse_teach_body(body)
    now = datetime.now(timezone.utc)
    factory = session_factory()
    with factory() as session:
        lot = _require_pool_lot(session, tender_id)
        state = session.get(LotState, tender_id)
        min_price = read_l1_min_price_rub(session)
        effective_before = _effective_tier(lot, state, min_price=min_price)
        expired_before = is_deadline_expired(lot.deadline_msk)
        event = TierTeachEvent(
            id=uuid4(),
            tender_id=tender_id,
            created_at=now,
            user_id=user_id,
            from_bucket=parsed["from_bucket"],
            to_bucket=parsed["to_bucket"],
            drop_tier_correct=parsed["drop_tier_correct"],
            reason_ru=parsed["reason_ru"],
            rules_tier=state.rules_tier if state is not None else lot.tier,
            ai_tier=state.ai_tier if state is not None else None,
            manual_tier_before=state.manual_tier if state is not None else None,
            effective_tier_before=effective_before,
            deadline_expired_before=expired_before,
            ai_reviewed=bool(state is not None and state.ai_reviewed_at is not None),
        )
        session.add(event)

        to_bucket = parsed["to_bucket"]
        if to_bucket in PRIORITY_TIERS:
            state = _ensure_lot_state(session, tender_id)
            state.manual_tier = to_bucket
            state.manual_tier_at = now

        session.commit()
        session.refresh(event)
        lot = session.get(Lot, tender_id)
        state = session.get(LotState, tender_id)
        docs = list(
            session.scalars(select(Document).where(Document.tender_id == tender_id)).all()
        )
        assert lot is not None
        return {
            "event_id": str(event.id),
            "lot": serialize_lot(
                lot, state, documents=docs, include_documents=True, min_price=min_price
            ),
        }


def list_tier_teach(*, limit: int | None = None) -> dict[str, Any]:
    from sqlalchemy import func as sa_func

    lim = TEACH_LIST_DEFAULT if limit is None else limit
    if not isinstance(lim, int) or isinstance(lim, bool) or lim < 1:
        raise InboxQueryError("invalid_limit")
    lim = min(lim, TEACH_LIST_MAX)
    factory = session_factory()
    with factory() as session:
        total = int(session.scalar(select(sa_func.count()).select_from(TierTeachEvent)) or 0)
        rows = list(
            session.scalars(
                select(TierTeachEvent)
                .order_by(TierTeachEvent.created_at.desc())
                .limit(lim)
            ).all()
        )
        items = [
            {
                "id": str(row.id),
                "tender_id": row.tender_id,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "user_id": str(row.user_id) if row.user_id else None,
                "from_bucket": row.from_bucket,
                "to_bucket": row.to_bucket,
                "drop_tier_correct": bool(row.drop_tier_correct),
                "reason_ru": row.reason_ru,
                "rules_tier": row.rules_tier,
                "ai_tier": row.ai_tier,
                "manual_tier_before": row.manual_tier_before,
                "effective_tier_before": row.effective_tier_before,
                "deadline_expired_before": bool(row.deadline_expired_before),
                "ai_reviewed": bool(row.ai_reviewed),
            }
            for row in rows
        ]
        return {"items": items, "total": total}


def send_lot_to_bitrix(tender_id: str) -> dict[str, Any]:
    """POST send → lead + chat; set bitrix_sent_at. Raises InboxConflict if already sent."""
    from app.bitrix import BitrixApiError, BitrixConfigError
    from app.bitrix.send import send_lead_and_chat
    from app.api.notify import notify_ops_event

    factory = session_factory()
    with factory() as session:
        lot = _require_pool_lot(session, tender_id)
        state = session.get(LotState, tender_id)
        if state is not None and state.bitrix_sent_at is not None:
            raise InboxConflict("already_sent")
        min_price = read_l1_min_price_rub(session)
        payload = serialize_lot(lot, state, min_price=min_price)
        # ensure inn from ORM (also on serialize now)
        payload["customer_inn"] = lot.customer_inn

    try:
        result = send_lead_and_chat(payload)
    except BitrixConfigError as exc:
        notify_ops_event(
            subject="лид не создан",
            body=f"ID: {tender_id}\nПричина: Битрикс не настроен",
        )
        raise InboxQueryError(str(exc) or "bitrix_unconfigured") from exc
    except BitrixApiError as exc:
        notify_ops_event(
            subject="лид не создан",
            body=f"ID: {tender_id}\nКод: {exc.code}",
        )
        raise InboxQueryError(exc.code) from exc

    now = datetime.now(timezone.utc)
    with factory() as session:
        lot = _require_pool_lot(session, tender_id)
        state = _ensure_lot_state(session, tender_id)
        if state.bitrix_sent_at is not None:
            raise InboxConflict("already_sent")
        state.bitrix_sent_at = now
        session.commit()
        min_price = read_l1_min_price_rub(session)
        docs = list(
            session.scalars(select(Document).where(Document.tender_id == tender_id)).all()
        )
        item = serialize_lot(
            lot, state, documents=docs, include_documents=True, min_price=min_price
        )
    return {
        "lead_id": result["lead_id"],
        "chat_message_id": result.get("chat_message_id"),
        "item": item,
    }

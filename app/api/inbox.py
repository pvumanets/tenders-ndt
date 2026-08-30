"""P5.4–P5.5 + P8–P10: Sales Inbox from Postgres (tier L1–L3). Does not read run JSON."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import quote

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.deadline import deadline_date, deadline_iso, is_deadline_expired, today_msk_date
from app.db.models import Document, Lot, LotState
from app.db.session import session_factory
from app.worker.ingest import INBOX_TIERS
from app.worker.customer_name import clean_customer_name
from app.worker.docs import resolve_volume_file, sanitize_filename

TIER_FILTERS = frozenset({"fit", "L1", "L2", "L3"})
PRIORITY_TIERS = frozenset({"L1", "L2", "L3"})


class InboxQueryError(ValueError):
    """Invalid query or body — map to HTTP 400."""


class InboxNotFound(LookupError):
    """Lot missing from the L1–L3 pool — map to HTTP 404."""


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


def _effective_tier(lot: Lot, state: LotState | None) -> str:
    if state is not None and state.manual_tier:
        return state.manual_tier
    if state is not None and state.ai_reviewed_at is not None and state.ai_tier in PRIORITY_TIERS:
        return state.ai_tier
    return lot.tier


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
) -> dict[str, Any]:
    due = deadline_date(lot.deadline_msk)
    today_d = today_msk_date(today)
    expired = due is not None and due < today_d
    payload: dict[str, Any] = {
        "tender_id": lot.tender_id,
        "title": lot.title,
        "customer_name": clean_customer_name(lot.customer_name),
        "score": lot.score,
        "tier": lot.tier,
        "effective_tier": _effective_tier(lot, state),
        "manual_tier": state.manual_tier if state is not None else None,
        "viewed": bool(state.viewed) if state is not None else False,
        "board_hidden": bool(state.board_hidden) if state is not None else False,
        "deadline_expired": expired,
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
        "rules_tier": (state.rules_tier if state is not None else None) or lot.tier,
        "ai_reviewed": bool(state is not None and state.ai_reviewed_at is not None),
        "ai_reviewed_at": ingested_iso(state.ai_reviewed_at) if state is not None else None,
        "ai_tier": state.ai_tier if state is not None else None,
        "ai_reason_ru": state.ai_reason_ru if state is not None else None,
        "ai_error": state.ai_error if state is not None else None,
        "ai_wrong": bool(state is not None and state.ai_wrong_at is not None),
        "ai_trigger": state.ai_trigger if state is not None else None,
    }
    if include_documents:
        rows = documents if documents is not None else []
        payload["documents"] = [_doc_meta(row) for row in rows]
    return payload


def _sort_key_live(lot: Lot) -> tuple[int, date, str]:
    due = deadline_date(lot.deadline_msk) or date.max
    return (-lot.score, due, lot.tender_id)


def _sort_key_expired(lot: Lot) -> tuple[date, str]:
    """Freshest expired first (deadline DESC)."""
    due = deadline_date(lot.deadline_msk) or date.min
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
    today: date | None = None,
) -> dict[str, Any]:
    unread_flag = parse_unread(unread)
    tier_filter = parse_tier_filter(tier)
    ai_flag = parse_ai_reviewed(ai_reviewed)
    trigger = parse_ai_trigger(ai_trigger)
    dl_from = parse_query_date(deadline_from)
    dl_to = parse_query_date(deadline_to)
    ing_from = parse_query_date(ingested_from)
    ing_to = parse_query_date(ingested_to)
    needle = (q or "").strip()
    today_d = today_msk_date(today)

    factory = session_factory()
    with factory() as session:
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
            due = deadline_date(lot.deadline_msk)
            if due is None:
                continue
            if tier_filter != "fit" and _effective_tier(lot, state) != tier_filter:
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
        live.sort(key=lambda pair: _sort_key_live(pair[0]))
        expired.sort(key=lambda pair: _sort_key_expired(pair[0]), reverse=True)
        filtered = live + expired
        items = [serialize_lot(lot, state, today=today_d) for lot, state in filtered]
        return {"items": items, "total": len(items)}


def _require_pool_lot(session, tender_id: str) -> Lot:
    lot = session.get(Lot, tender_id)
    if lot is None or not _in_pool(lot):
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
    from app.ai.provod import AiTierError, review_tier
    from app.api.notify import notify_auto_l1
    from app.api.state import STATE

    factory = session_factory()
    processed = 0
    failed = 0
    items: list[dict[str, Any]] = []
    l1_ids: list[str] = []
    work = list(pairs)
    STATE.set_ai_progress(0, len(work))
    with factory() as session:
        for index, (lot, state) in enumerate(work):
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
                )
                state.ai_tier = result.tier
                state.ai_reason_ru = result.reason_ru
                state.ai_reviewed_at = now
                state.ai_error = None
                state.ai_trigger = trigger
                processed += 1
                if trigger == "auto" and result.tier == "L1":
                    l1_ids.append(lot.tender_id)
            except AiTierError as exc:
                state.ai_error = str(exc.message)
                failed += 1
            session.flush()
            session.commit()
            docs = list(
                session.scalars(select(Document).where(Document.tender_id == lot.tender_id)).all()
            )
            items.append(
                serialize_lot(lot, state, documents=docs, include_documents=True)
            )
            STATE.set_ai_progress(index + 1, len(work))

    STATE.set_ai_failures(failed)
    if failed:
        STATE.log_msg(f"ИИ: сбоев {failed}, успешно {processed}", level="warn")
    else:
        STATE.log_msg(f"ИИ: разобрано {processed}")
    if trigger == "auto":
        notify_auto_l1(l1_ids)
    return {"processed": processed, "failed": failed, "items": items}


def run_ai_review(body: Any) -> dict[str, Any]:
    """POST /api/inbox/ai-review — operator-triggered; never called from runner."""
    ids: list[str] | None = None
    if body is None or body == {}:
        ids = None
    elif isinstance(body, dict):
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
            pairs = list(session.execute(stmt).all())
        else:
            pairs = []
            for tid in ids:
                lot = session.get(Lot, tid)
                if lot is None or not _in_pool(lot):
                    failed_missing += 1
                    continue
                pairs.append((lot, session.get(LotState, tid)))

    result = _apply_ai_review(pairs, trigger="manual")
    result["failed"] = int(result.get("failed") or 0) + failed_missing
    return result


def run_auto_ai_review(prefer_ids: set[str]) -> dict[str, Any]:
    """After auto queue: prefer ∩ eligible. Empty prefer → no-op. Sets ai_trigger=auto."""
    from app.api.state import STATE

    if not prefer_ids:
        STATE.log_msg("Auto AI: no-op (empty prefer)")
        return {"processed": 0, "failed": 0, "items": []}
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
        STATE.log_msg("Auto AI: no-op (no eligible lots)")
        return {"processed": 0, "failed": 0, "items": []}
    return _apply_ai_review(pairs, trigger="auto", skip_hidden_expired=False)


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
        docs = list(
            session.scalars(select(Document).where(Document.tender_id == tender_id)).all()
        )
        return serialize_lot(lot, state, documents=docs, include_documents=True)
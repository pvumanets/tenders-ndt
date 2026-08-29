"""P5.3 + P9: ingest runs + lots (score ≥ 4). Update-on-diff; never touches lot_state."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.deadline import deadline_date, today_msk_date
from app.db.config import database_url
from app.db.models import Lot, Run
from app.db.session import session_factory
from app.worker.artifacts import _clean_loc
from app.worker.customer_name import clean_customer_name
from app.worker.etp_twins import hide_if_roseltorg_exists, hide_rostender_twins_for_roseltorg
from app.worker.platform_ids import PLATFORM_ROSELTORG, PLATFORM_ROSTENDER

INBOX_TIERS = frozenset({"L1", "L2", "L3"})
# Deprecated alias — pool is tier-based (P10/029), not score≥4.
INBOX_MIN_SCORE = 4
SOURCE_PLATFORM_ID = "rostender"
_RAW_KEYS = (
    "tender_id",
    "title",
    "url",
    "score",
    "tier",
    "rank",
    "fit_reason",
    "location",
    "customer_name",
    "customer_inn",
    "customer_kpp",
    "deadline_msk",
    "status",
    "price_rub",
    "source_etp",
    "source_platform_id",
    "etp_procedure_id",
    "methods",
    "contact_name",
    "contact_phone",
    "contact_email",
    "card_fetched",
    "card_error",
    "doc_links",
    "fit_extra",
    "notes",
)


@dataclass(frozen=True)
class IngestResult:
    run_id: UUID
    lot_count: int
    new_count: int = 0
    already_count: int = 0
    updated_count: int = 0


def inbox_rows(rows: list[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for row in rows:
        tier = str(row.get("tier") or "").strip()
        if tier not in INBOX_TIERS:
            continue
        tender_id = str(row.get("tender_id") or "").strip()
        title = str(row.get("title") or "").strip()
        url = str(row.get("url") or "").strip()
        if not tender_id or not title or not url:
            continue
        by_id[tender_id] = row
    return list(by_id.values())


def parse_price_rub(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return _bounded_price(value)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return _bounded_price(Decimal(value))
    if isinstance(value, float):
        return _bounded_price(Decimal(str(value)))
    digits = re.sub(r"[^\d,.\-]", "", str(value)).replace(" ", "")
    if not digits or digits in {".", "-", "-.", ".-"}:
        return None
    if digits.count(",") == 1 and digits.count(".") == 0:
        digits = digits.replace(",", ".")
    elif "," in digits:
        digits = digits.replace(",", "")
    try:
        return _bounded_price(Decimal(digits))
    except (InvalidOperation, ValueError):
        return None


def _bounded_price(value: Decimal) -> Decimal | None:
    quantized = value.quantize(Decimal("0.01"))
    # Numeric(14, 2) — 12 digits left of the decimal
    if quantized.copy_abs() >= Decimal("10") ** 12:
        return None
    return quantized


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _raw_payload(row: dict) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key in _RAW_KEYS:
        if key not in row:
            continue
        value = row[key]
        if value is None or isinstance(value, (str, int, float, bool, list, dict)):
            payload[key] = value
        else:
            payload[key] = str(value)
    return payload


def _doc_fingerprint(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, dict):
        return ()
    links = raw.get("doc_links")
    if not isinstance(links, list):
        return ()
    names: list[str] = []
    for item in links:
        if isinstance(item, str) and item.strip():
            names.append(item.strip())
        elif isinstance(item, dict):
            for key in ("name", "filename", "url", "href"):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    names.append(val.strip())
                    break
    return tuple(sorted(names))


def lot_differs(existing: Lot, values: dict[str, Any], row: dict) -> bool:
    """True when platform fields we care about changed (P9 update-on-diff)."""
    if (existing.title or "") != (values.get("title") or ""):
        return True
    if (existing.deadline_msk or None) != (values.get("deadline_msk") or None):
        return True
    old_price = existing.price_rub
    new_price = values.get("price_rub")
    if old_price is None and new_price is None:
        pass
    elif old_price is None or new_price is None or old_price != new_price:
        return True
    if _doc_fingerprint(existing.raw) != _doc_fingerprint(_raw_payload(row)):
        return True
    return False


def lot_values(
    row: dict,
    *,
    run_id: UUID,
    ingested_at: datetime,
    source_platform_id: str = SOURCE_PLATFORM_ID,
) -> dict[str, Any]:
    location = _clean_loc(_optional_text(row.get("location")) or "") or None
    try:
        score = int(row["score"])
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError("lot_score_invalid") from exc
    return {
        "tender_id": str(row["tender_id"]).strip(),
        "run_id": run_id,
        "title": str(row["title"]).strip(),
        "url": str(row["url"]).strip(),
        "score": score,
        "tier": str(row.get("tier") or "").strip() or "pool",
        "location": location,
        "customer_name": clean_customer_name(row.get("customer_name")),
        "customer_inn": _optional_text(row.get("customer_inn")),
        "deadline_msk": _optional_text(row.get("deadline_msk")),
        "status": _optional_text(row.get("status")),
        "price_rub": parse_price_rub(row.get("price_rub")),
        "fit_reason": _optional_text(row.get("fit_reason")),
        "source_platform_id": source_platform_id,
        "contact_name": _optional_text(row.get("contact_name")),
        "contact_phone": _optional_text(row.get("contact_phone")),
        "contact_email": _optional_text(row.get("contact_email")),
        "raw": _raw_payload(row),
        "ingested_at": ingested_at,
    }


def expired_tender_ids(
    session: Session,
    *,
    today: date | None = None,
) -> set[str]:
    """Inbox-pool lots whose deadline is strictly before today (MSK)."""
    today_d = today_msk_date(today)
    rows = session.scalars(select(Lot).where(Lot.tier.in_(tuple(INBOX_TIERS)))).all()
    out: set[str] = set()
    for lot in rows:
        due = deadline_date(lot.deadline_msk)
        if due is not None and due < today_d:
            out.add(lot.tender_id)
    return out


def snapshot_expired_tender_ids(*, today: date | None = None) -> set[str]:
    if not database_url():
        return set()
    factory = session_factory()
    with factory() as session:
        return expired_tender_ids(session, today=today)


def ingest_run(
    *,
    query: str,
    limit_n: int,
    status: str,
    rows: list[dict],
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    source_platform_id: str = SOURCE_PLATFORM_ID,
    search_id: UUID | None = None,
) -> IngestResult | None:
    """Write one run + insert/update-on-diff inbox lots. None if DATABASE_URL is unset."""
    if not database_url():
        return None
    now = datetime.now(timezone.utc)
    started = started_at or now
    finished = finished_at or now
    candidates = inbox_rows(rows)
    factory = session_factory()
    with factory() as session:
        run = Run(
            query=query,
            status=status,
            limit_n=limit_n,
            source_platform_id=source_platform_id,
            search_id=search_id,
            started_at=started,
            finished_at=finished,
        )
        session.add(run)
        session.flush()

        new_count = 0
        already_count = 0
        updated_count = 0
        if candidates:
            values_list = [
                lot_values(
                    row,
                    run_id=run.id,
                    ingested_at=now,
                    source_platform_id=source_platform_id,
                )
                for row in candidates
            ]
            ids = [v["tender_id"] for v in values_list]
            existing = {
                lot.tender_id: lot
                for lot in session.scalars(select(Lot).where(Lot.tender_id.in_(ids))).all()
            }
            to_insert: list[dict[str, Any]] = []
            to_update: list[tuple[dict[str, Any], dict]] = []
            for row, vals in zip(candidates, values_list, strict=True):
                old = existing.get(vals["tender_id"])
                if old is None:
                    to_insert.append(vals)
                    new_count += 1
                elif lot_differs(old, vals, row):
                    to_update.append((vals, row))
                    updated_count += 1
                else:
                    already_count += 1

            if to_insert:
                session.execute(pg_insert(Lot).values(to_insert))
            for vals, _row in to_update:
                lot = existing[vals["tender_id"]]
                for key, value in vals.items():
                    if key == "tender_id":
                        continue
                    setattr(lot, key, value)

        if source_platform_id == PLATFORM_ROSELTORG and candidates:
            natives = [
                str(row.get("etp_procedure_id") or str(row.get("tender_id") or "").split(":")[-1])
                for row in candidates
            ]
            hide_rostender_twins_for_roseltorg(session, native_ids=natives)
        elif source_platform_id == PLATFORM_ROSTENDER and candidates:
            for row in candidates:
                hide_if_roseltorg_exists(session, rostender_row=row)

        session.commit()
        return IngestResult(
            run_id=run.id,
            lot_count=len(candidates),
            new_count=new_count,
            already_count=already_count,
            updated_count=updated_count,
        )


def redact_db_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    url = database_url()
    if url:
        text = text.replace(url, "DATABASE_URL")
    return text

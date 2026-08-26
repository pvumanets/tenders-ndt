"""P5.3: upsert runs + lots (score ≥ 4) after a pipeline. Never touches lot_state."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.config import database_url
from app.db.models import Lot, Run
from app.db.session import session_factory
from app.worker.artifacts import _clean_loc
from app.worker.customer_name import clean_customer_name

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
    "methods",
    "contact_name",
    "contact_phone",
    "contact_email",
    "card_fetched",
    "card_error",
    "doc_links",
    "notes",
)


@dataclass(frozen=True)
class IngestResult:
    run_id: UUID
    lot_count: int


def inbox_rows(rows: list[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for row in rows:
        try:
            score = int(row.get("score") or 0)
        except (TypeError, ValueError):
            continue
        if score < INBOX_MIN_SCORE:
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
    """Write one run + upsert inbox lots. None if DATABASE_URL is unset."""
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
        if candidates:
            values = [
                lot_values(
                    row,
                    run_id=run.id,
                    ingested_at=now,
                    source_platform_id=source_platform_id,
                )
                for row in candidates
            ]
            stmt = pg_insert(Lot).values(values)
            excluded = stmt.excluded
            update = {
                column.name: getattr(excluded, column.name)
                for column in Lot.__table__.columns
                if column.name != "tender_id"
            }
            session.execute(
                stmt.on_conflict_do_update(index_elements=["tender_id"], set_=update)
            )
        session.commit()
        return IngestResult(run_id=run.id, lot_count=len(candidates))


def redact_db_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    url = database_url()
    if url:
        text = text.replace(url, "DATABASE_URL")
    return text

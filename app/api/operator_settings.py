"""Operator inbox settings — GET/PUT /api/operator-settings (singleton id=1)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db.models import OperatorSettings
from app.db.session import session_factory

SETTINGS_ID = 1
DEFAULT_L1_MIN_PRICE_RUB = 100_000
MIN_L1_MIN_PRICE_RUB = 0
MAX_L1_MIN_PRICE_RUB = 5_000_000


class OperatorSettingsError(ValueError):
    """Invalid operator settings payload — map to HTTP 400."""


def _ensure_row(session) -> OperatorSettings:
    row = session.get(OperatorSettings, SETTINGS_ID)
    if row is not None:
        return row
    row = OperatorSettings(
        id=SETTINGS_ID,
        l1_min_price_rub=DEFAULT_L1_MIN_PRICE_RUB,
    )
    session.add(row)
    session.flush()
    return row


def _row_payload(row: OperatorSettings) -> dict[str, Any]:
    return {"l1_min_price_rub": int(row.l1_min_price_rub)}


def parse_l1_min_price_rub(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise OperatorSettingsError("invalid_l1_min_price_rub")
    if value < MIN_L1_MIN_PRICE_RUB or value > MAX_L1_MIN_PRICE_RUB:
        raise OperatorSettingsError("invalid_l1_min_price_rub")
    return value


def get_operator_settings() -> dict[str, Any]:
    factory = session_factory()
    with factory() as session:
        row = _ensure_row(session)
        session.commit()
        return _row_payload(row)


def put_operator_settings(body: dict[str, Any] | None) -> dict[str, Any]:
    payload = body if isinstance(body, dict) else {}
    if "l1_min_price_rub" not in payload:
        raise OperatorSettingsError("invalid_l1_min_price_rub")
    price = parse_l1_min_price_rub(payload["l1_min_price_rub"])
    factory = session_factory()
    with factory() as session:
        row = _ensure_row(session)
        row.l1_min_price_rub = price
        row.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(row)
        return _row_payload(row)


def read_l1_min_price_rub(session) -> int:
    row = session.get(OperatorSettings, SETTINGS_ID)
    if row is None:
        return DEFAULT_L1_MIN_PRICE_RUB
    return int(row.l1_min_price_rub)

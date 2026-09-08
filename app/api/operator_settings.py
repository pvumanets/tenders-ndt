"""Operator inbox settings — GET/PUT /api/operator-settings (singleton id=1)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.ai.provod import DEFAULT_SYSTEM_PROMPT
from app.db.models import OperatorSettings
from app.db.session import session_factory

SETTINGS_ID = 1
DEFAULT_L1_MIN_PRICE_RUB = 100_000
MIN_L1_MIN_PRICE_RUB = 0
MAX_L1_MIN_PRICE_RUB = 5_000_000
MAX_AI_SYSTEM_PROMPT_LEN = 50_000


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


def _effective_prompt(row: OperatorSettings) -> tuple[str, bool]:
    stored = row.ai_system_prompt
    if stored is None:
        return DEFAULT_SYSTEM_PROMPT, True
    text = stored.strip()
    if not text:
        return DEFAULT_SYSTEM_PROMPT, True
    return text, False


def _row_payload(row: OperatorSettings) -> dict[str, Any]:
    prompt, is_default = _effective_prompt(row)
    return {
        "l1_min_price_rub": int(row.l1_min_price_rub),
        "ai_system_prompt": prompt,
        "ai_system_prompt_is_default": is_default,
    }


def parse_l1_min_price_rub(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise OperatorSettingsError("invalid_l1_min_price_rub")
    if value < MIN_L1_MIN_PRICE_RUB or value > MAX_L1_MIN_PRICE_RUB:
        raise OperatorSettingsError("invalid_l1_min_price_rub")
    return value


def parse_ai_system_prompt(value: Any) -> str | None:
    """None = reset to default. Non-empty str = store override."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise OperatorSettingsError("invalid_ai_system_prompt")
    text = value.strip()
    if not text:
        raise OperatorSettingsError("invalid_ai_system_prompt")
    if len(text) > MAX_AI_SYSTEM_PROMPT_LEN:
        raise OperatorSettingsError("invalid_ai_system_prompt")
    return text


def get_operator_settings() -> dict[str, Any]:
    factory = session_factory()
    with factory() as session:
        row = _ensure_row(session)
        session.commit()
        return _row_payload(row)


def put_operator_settings(body: dict[str, Any] | None) -> dict[str, Any]:
    payload = body if isinstance(body, dict) else {}
    has_price = "l1_min_price_rub" in payload
    has_prompt = "ai_system_prompt" in payload
    if not has_price and not has_prompt:
        raise OperatorSettingsError("invalid_body")

    price: int | None = None
    if has_price:
        price = parse_l1_min_price_rub(payload["l1_min_price_rub"])

    prompt_value: str | None | object = ...
    if has_prompt:
        prompt_value = parse_ai_system_prompt(payload["ai_system_prompt"])

    factory = session_factory()
    with factory() as session:
        row = _ensure_row(session)
        if price is not None:
            row.l1_min_price_rub = price
        if has_prompt:
            row.ai_system_prompt = prompt_value  # type: ignore[assignment]
        row.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(row)
        return _row_payload(row)


def read_l1_min_price_rub(session) -> int:
    row = session.get(OperatorSettings, SETTINGS_ID)
    if row is None:
        return DEFAULT_L1_MIN_PRICE_RUB
    return int(row.l1_min_price_rub)


def read_ai_system_prompt(session) -> str:
    row = session.get(OperatorSettings, SETTINGS_ID)
    if row is None:
        return DEFAULT_SYSTEM_PROMPT
    prompt, _ = _effective_prompt(row)
    return prompt

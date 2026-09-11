"""Operator inbox settings — GET/PUT /api/operator-settings (singleton id=1)."""
from __future__ import annotations

import os
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
MAX_SECRET_LEN = 2_000
MAX_ID_LEN = 128

ENV_PROVOD_API_KEY = "PROVOD_API_KEY"
ENV_BITRIX_WEBHOOK = "BITRIX_WEBHOOK_URL"
ENV_BITRIX_ASSIGNED = "BITRIX_ASSIGNED_BY_ID"
ENV_BITRIX_SOURCE = "BITRIX_LEAD_SOURCE_ID"
ENV_BITRIX_CHAT = "BITRIX_CHAT_DIALOG_ID"
ENV_BITRIX_OPS = "BITRIX_OPS_DIALOG_ID"
ENV_BITRIX_SEND_CHAT = "BITRIX_SEND_CHAT"

SECRET_KEYS = frozenset({"provod_api_key", "bitrix_webhook_url"})
ID_KEYS = frozenset(
    {
        "bitrix_assigned_by_id",
        "bitrix_lead_source_id",
        "bitrix_chat_dialog_id",
        "bitrix_ops_dialog_id",
    }
)
TOGGLE_KEYS = frozenset(
    {
        "bitrix_send_chat",
        "bitrix_auto_l1_enabled",
        "bitrix_ops_alerts_enabled",
    }
)


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


def _env_str(name: str) -> str:
    return (os.getenv(name) or "").strip()


def _db_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def mask_secret(raw: str | None) -> dict[str, Any]:
    """Never return plaintext — only configured + hint."""
    text = (raw or "").strip()
    if not text:
        return {"configured": False, "hint": ""}
    if len(text) < 8:
        return {"configured": True, "hint": "••••"}
    return {"configured": True, "hint": f"••••{text[-4:]}"}


def _effective_secret(db_val: str | None, env_name: str) -> str:
    stored = _db_text(db_val)
    if stored:
        return stored
    return _env_str(env_name)


def _effective_id(db_val: str | None, env_name: str) -> str:
    stored = _db_text(db_val)
    if stored is not None:
        return stored
    return _env_str(env_name)


def _env_bool(name: str) -> bool | None:
    raw = (os.getenv(name) or "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return None


def _effective_toggle(db_val: bool | None, *, env_name: str | None, default: bool) -> bool:
    if db_val is not None:
        return bool(db_val)
    if env_name:
        env_val = _env_bool(env_name)
        if env_val is not None:
            return env_val
    return default


def _row_integrations(row: OperatorSettings) -> dict[str, Any]:
    provod = _effective_secret(row.provod_api_key, ENV_PROVOD_API_KEY)
    webhook = _effective_secret(row.bitrix_webhook_url, ENV_BITRIX_WEBHOOK)
    return {
        "provod_api_key": mask_secret(provod),
        "bitrix_webhook_url": mask_secret(webhook),
        "bitrix_assigned_by_id": _effective_id(row.bitrix_assigned_by_id, ENV_BITRIX_ASSIGNED),
        "bitrix_lead_source_id": _effective_id(row.bitrix_lead_source_id, ENV_BITRIX_SOURCE),
        "bitrix_chat_dialog_id": _effective_id(row.bitrix_chat_dialog_id, ENV_BITRIX_CHAT),
        "bitrix_ops_dialog_id": _effective_id(row.bitrix_ops_dialog_id, ENV_BITRIX_OPS),
        "bitrix_send_chat": _effective_toggle(
            row.bitrix_send_chat, env_name=ENV_BITRIX_SEND_CHAT, default=True
        ),
        "bitrix_auto_l1_enabled": _effective_toggle(
            row.bitrix_auto_l1_enabled, env_name=None, default=True
        ),
        "bitrix_ops_alerts_enabled": _effective_toggle(
            row.bitrix_ops_alerts_enabled, env_name=None, default=True
        ),
    }


def _row_payload(row: OperatorSettings) -> dict[str, Any]:
    prompt, is_default = _effective_prompt(row)
    payload = {
        "l1_min_price_rub": int(row.l1_min_price_rub),
        "ai_system_prompt": prompt,
        "ai_system_prompt_is_default": is_default,
    }
    payload.update(_row_integrations(row))
    return payload


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


def parse_secret_field(key: str, value: Any) -> str | None:
    """None = clear DB override. Non-empty str = store."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise OperatorSettingsError(f"invalid_{key}")
    text = value.strip()
    if not text:
        raise OperatorSettingsError(f"invalid_{key}")
    if len(text) > MAX_SECRET_LEN:
        raise OperatorSettingsError(f"invalid_{key}")
    return text


def parse_id_field(key: str, value: Any) -> str | None:
    """None or blank = clear DB override. Non-empty str = store."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise OperatorSettingsError(f"invalid_{key}")
    text = value.strip()
    if not text:
        return None
    if len(text) > MAX_ID_LEN:
        raise OperatorSettingsError(f"invalid_{key}")
    return text


def parse_toggle_field(key: str, value: Any) -> bool | None:
    """None = clear DB override (fall back to env/default)."""
    if value is None:
        return None
    if not isinstance(value, bool):
        raise OperatorSettingsError(f"invalid_{key}")
    return value


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
    secret_updates = {k: payload[k] for k in SECRET_KEYS if k in payload}
    id_updates = {k: payload[k] for k in ID_KEYS if k in payload}
    toggle_updates = {k: payload[k] for k in TOGGLE_KEYS if k in payload}
    if not (
        has_price
        or has_prompt
        or secret_updates
        or id_updates
        or toggle_updates
    ):
        raise OperatorSettingsError("invalid_body")

    price: int | None = None
    if has_price:
        price = parse_l1_min_price_rub(payload["l1_min_price_rub"])

    prompt_value: str | None | object = ...
    if has_prompt:
        prompt_value = parse_ai_system_prompt(payload["ai_system_prompt"])

    parsed_secrets = {
        key: parse_secret_field(key, val) for key, val in secret_updates.items()
    }
    parsed_ids = {key: parse_id_field(key, val) for key, val in id_updates.items()}
    parsed_toggles = {
        key: parse_toggle_field(key, val) for key, val in toggle_updates.items()
    }

    factory = session_factory()
    with factory() as session:
        row = _ensure_row(session)
        if price is not None:
            row.l1_min_price_rub = price
        if has_prompt:
            row.ai_system_prompt = prompt_value  # type: ignore[assignment]
        for key, val in parsed_secrets.items():
            setattr(row, key, val)
        for key, val in parsed_ids.items():
            setattr(row, key, val)
        for key, val in parsed_toggles.items():
            setattr(row, key, val)
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


def _read_row_or_none():
    try:
        factory = session_factory()
    except RuntimeError:
        return None
    with factory() as session:
        return session.get(OperatorSettings, SETTINGS_ID)


def resolve_provod_api_key() -> str | None:
    row = _read_row_or_none()
    db_val = row.provod_api_key if row is not None else None
    text = _effective_secret(db_val, ENV_PROVOD_API_KEY)
    return text or None


def resolve_bitrix_webhook_url() -> str | None:
    row = _read_row_or_none()
    db_val = row.bitrix_webhook_url if row is not None else None
    text = _effective_secret(db_val, ENV_BITRIX_WEBHOOK)
    return text or None


def resolve_bitrix_lead_source_id() -> str | None:
    row = _read_row_or_none()
    db_val = row.bitrix_lead_source_id if row is not None else None
    text = _effective_id(db_val, ENV_BITRIX_SOURCE)
    return text or None


def resolve_bitrix_chat_dialog_id() -> str | None:
    row = _read_row_or_none()
    db_val = row.bitrix_chat_dialog_id if row is not None else None
    text = _effective_id(db_val, ENV_BITRIX_CHAT)
    return text or None


def resolve_bitrix_ops_dialog_id() -> str | None:
    row = _read_row_or_none()
    db_val = row.bitrix_ops_dialog_id if row is not None else None
    text = _effective_id(db_val, ENV_BITRIX_OPS)
    return text or None


def resolve_bitrix_assigned_by_id() -> str | None:
    row = _read_row_or_none()
    db_val = row.bitrix_assigned_by_id if row is not None else None
    text = _effective_id(db_val, ENV_BITRIX_ASSIGNED)
    return text or None


def resolve_bitrix_send_chat() -> bool:
    row = _read_row_or_none()
    db_val = row.bitrix_send_chat if row is not None else None
    return _effective_toggle(db_val, env_name=ENV_BITRIX_SEND_CHAT, default=True)


def resolve_bitrix_auto_l1_enabled() -> bool:
    row = _read_row_or_none()
    db_val = row.bitrix_auto_l1_enabled if row is not None else None
    return _effective_toggle(db_val, env_name=None, default=True)


def resolve_bitrix_ops_alerts_enabled() -> bool:
    row = _read_row_or_none()
    db_val = row.bitrix_ops_alerts_enabled if row is not None else None
    return _effective_toggle(db_val, env_name=None, default=True)

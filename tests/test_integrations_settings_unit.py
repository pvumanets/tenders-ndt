"""Unit: integrations secrets/IDs/toggles in operator_settings (111)."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.api.operator_settings import (
    OperatorSettingsError,
    mask_secret,
    parse_id_field,
    parse_secret_field,
    parse_toggle_field,
    put_operator_settings,
    resolve_bitrix_auto_l1_enabled,
    resolve_bitrix_send_chat,
    resolve_provod_api_key,
)
from app.bitrix import auto_leads
from app.bitrix import send as bitrix_send


@pytest.mark.unit
def test_mask_secret_never_full() -> None:
    assert mask_secret(None) == {"configured": False, "hint": ""}
    assert mask_secret("") == {"configured": False, "hint": ""}
    assert mask_secret("short") == {"configured": True, "hint": "••••"}
    out = mask_secret("sk_live_abcdef12")
    assert out["configured"] is True
    assert out["hint"] == "••••ef12"
    assert "sk_live" not in out["hint"]
    assert "abcdef" not in out["hint"]


@pytest.mark.unit
def test_parse_secret_and_id_and_toggle() -> None:
    assert parse_secret_field("provod_api_key", None) is None
    assert parse_secret_field("provod_api_key", "  abc  ") == "abc"
    with pytest.raises(OperatorSettingsError, match="invalid_provod_api_key"):
        parse_secret_field("provod_api_key", "")
    with pytest.raises(OperatorSettingsError, match="invalid_provod_api_key"):
        parse_secret_field("provod_api_key", 1)

    assert parse_id_field("bitrix_chat_dialog_id", None) is None
    assert parse_id_field("bitrix_chat_dialog_id", "  ") is None
    assert parse_id_field("bitrix_chat_dialog_id", "chat7543") == "chat7543"

    assert parse_toggle_field("bitrix_send_chat", None) is None
    assert parse_toggle_field("bitrix_send_chat", True) is True
    with pytest.raises(OperatorSettingsError, match="invalid_bitrix_send_chat"):
        parse_toggle_field("bitrix_send_chat", 1)


@pytest.mark.unit
def test_resolve_env_fallback_without_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.api.operator_settings.session_factory",
        lambda: (_ for _ in ()).throw(RuntimeError("database_unconfigured")),
    )
    monkeypatch.setenv("PROVOD_API_KEY", "env_key_value_99")
    monkeypatch.delenv("BITRIX_SEND_CHAT", raising=False)
    assert resolve_provod_api_key() == "env_key_value_99"
    assert resolve_bitrix_send_chat() is True
    monkeypatch.setenv("BITRIX_SEND_CHAT", "0")
    assert resolve_bitrix_send_chat() is False
    assert resolve_bitrix_auto_l1_enabled() is True


@pytest.mark.unit
def test_resolve_db_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    row = SimpleNamespace(
        provod_api_key="db_secret_key_xx",
        bitrix_send_chat=False,
        bitrix_auto_l1_enabled=False,
        bitrix_ops_alerts_enabled=True,
        bitrix_webhook_url=None,
        bitrix_assigned_by_id=None,
        bitrix_lead_source_id=None,
        bitrix_chat_dialog_id=None,
        bitrix_ops_dialog_id=None,
    )

    class _Sess:
        def get(self, *_a: object, **_k: object) -> Any:
            return row

        def __enter__(self) -> "_Sess":
            return self

        def __exit__(self, *_a: object) -> None:
            return None

    monkeypatch.setattr(
        "app.api.operator_settings.session_factory",
        lambda: (lambda: _Sess()),
    )
    monkeypatch.setenv("PROVOD_API_KEY", "env_should_lose")
    monkeypatch.setenv("BITRIX_SEND_CHAT", "1")
    assert resolve_provod_api_key() == "db_secret_key_xx"
    assert resolve_bitrix_send_chat() is False
    assert resolve_bitrix_auto_l1_enabled() is False


@pytest.mark.unit
def test_put_integrations_writes_and_masks(monkeypatch: pytest.MonkeyPatch) -> None:
    row = SimpleNamespace(
        id=1,
        l1_min_price_rub=100_000,
        ai_system_prompt=None,
        provod_api_key=None,
        bitrix_webhook_url=None,
        bitrix_assigned_by_id=None,
        bitrix_lead_source_id=None,
        bitrix_chat_dialog_id=None,
        bitrix_ops_dialog_id=None,
        bitrix_send_chat=None,
        bitrix_auto_l1_enabled=None,
        bitrix_ops_alerts_enabled=None,
        updated_at=None,
    )

    class _Sess:
        def get(self, *_a: object, **_k: object) -> Any:
            return row

        def commit(self) -> None:
            return None

        def refresh(self, *_a: object) -> None:
            return None

        def __enter__(self) -> "_Sess":
            return self

        def __exit__(self, *_a: object) -> None:
            return None

    monkeypatch.setattr(
        "app.api.operator_settings.session_factory",
        lambda: (lambda: _Sess()),
    )
    monkeypatch.delenv("PROVOD_API_KEY", raising=False)
    monkeypatch.delenv("BITRIX_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("BITRIX_ASSIGNED_BY_ID", raising=False)
    monkeypatch.delenv("BITRIX_LEAD_SOURCE_ID", raising=False)
    monkeypatch.delenv("BITRIX_CHAT_DIALOG_ID", raising=False)
    monkeypatch.delenv("BITRIX_OPS_DIALOG_ID", raising=False)
    monkeypatch.delenv("BITRIX_SEND_CHAT", raising=False)

    secret = "sk_test_abcdefghij"
    webhook = "https://example.test/rest/1/tokensecret/"
    out = put_operator_settings(
        {
            "provod_api_key": secret,
            "bitrix_webhook_url": webhook,
            "bitrix_assigned_by_id": "71",
            "bitrix_lead_source_id": "TENDERS_UMANETS",
            "bitrix_chat_dialog_id": "chat7543",
            "bitrix_ops_dialog_id": "951",
            "bitrix_send_chat": False,
            "bitrix_auto_l1_enabled": False,
            "bitrix_ops_alerts_enabled": False,
        }
    )
    assert row.provod_api_key == secret
    assert row.bitrix_webhook_url == webhook
    assert row.bitrix_assigned_by_id == "71"
    assert row.bitrix_send_chat is False
    assert row.bitrix_auto_l1_enabled is False
    assert out["provod_api_key"] == {"configured": True, "hint": "••••ghij"}
    assert out["bitrix_webhook_url"]["configured"] is True
    assert secret not in str(out)
    assert "tokensecret" not in str(out)
    assert out["bitrix_chat_dialog_id"] == "chat7543"
    assert out["bitrix_send_chat"] is False
    assert out["bitrix_auto_l1_enabled"] is False

    cleared = put_operator_settings(
        {
            "provod_api_key": None,
            "bitrix_webhook_url": None,
            "bitrix_assigned_by_id": None,
            "bitrix_lead_source_id": None,
            "bitrix_chat_dialog_id": None,
            "bitrix_ops_dialog_id": None,
            "bitrix_send_chat": None,
            "bitrix_auto_l1_enabled": None,
            "bitrix_ops_alerts_enabled": None,
        }
    )
    assert row.provod_api_key is None
    assert row.bitrix_send_chat is None
    assert cleared["provod_api_key"] == {"configured": False, "hint": ""}
    assert cleared["bitrix_send_chat"] is True
    assert cleared["bitrix_auto_l1_enabled"] is True


@pytest.mark.unit
def test_ops_dm_skipped_when_alerts_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.api.operator_settings.resolve_bitrix_ops_alerts_enabled",
        lambda: False,
    )
    assert bitrix_send.send_ops_dm("x") == "skipped"


@pytest.mark.unit
def test_auto_l1_skipped_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.api.operator_settings.resolve_bitrix_auto_l1_enabled",
        lambda: False,
    )
    counts = auto_leads.notify_auto_l1_leads(["rostender:1", "rostender:2"])
    assert counts == {"sent": 0, "skipped": 2, "failed": 0}

"""Unit tests for Bitrix send / ops DM / digest — no live webhook."""
from __future__ import annotations

import pytest

from app.bitrix import BitrixApiError, BitrixConfigError
from app.bitrix import send as bitrix_send


def _no_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.api.operator_settings.session_factory",
        lambda: (_ for _ in ()).throw(RuntimeError("database_unconfigured")),
    )


@pytest.mark.unit
def test_chat_send_enabled_default_on(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_db(monkeypatch)
    monkeypatch.delenv("BITRIX_SEND_CHAT", raising=False)
    assert bitrix_send.chat_send_enabled() is True
    monkeypatch.setenv("BITRIX_SEND_CHAT", "0")
    assert bitrix_send.chat_send_enabled() is False


@pytest.mark.unit
def test_send_lead_and_chat_calls_lead_and_im(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_db(monkeypatch)
    monkeypatch.setenv("BITRIX_WEBHOOK_URL", "https://example.test/rest/1/x/")
    monkeypatch.setenv("BITRIX_SEND_CHAT", "1")
    monkeypatch.setenv("BITRIX_LEAD_SOURCE_ID", "TEST_SOURCE")
    monkeypatch.setenv("BITRIX_CHAT_DIALOG_ID", "chat7543")
    calls: list[tuple[str, dict]] = []

    def fake_call(method: str, params: dict) -> object:
        calls.append((method, params))
        if method == "crm.lead.add":
            return 7001
        if method == "im.message.add":
            return 42
        return None

    monkeypatch.setattr(bitrix_send, "call_method", fake_call)
    out = bitrix_send.send_lead_and_chat(
        {
            "tender_id": "rostender:1",
            "title": "УЗК",
            "customer_name": "ООО",
            "effective_tier": "L1",
            "source_platform_id": "rostender",
        }
    )
    assert out["lead_id"] == 7001
    assert out["chat_message_id"] == 42
    assert calls[0][0] == "crm.lead.add"
    assert calls[1][0] == "im.message.add"
    assert calls[1][1]["DIALOG_ID"] == "chat7543"
    assert "Scout" not in calls[1][1]["MESSAGE"]
    assert "Разведчик" in calls[1][1]["MESSAGE"]


@pytest.mark.unit
def test_send_ops_dm_uses_env_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_db(monkeypatch)
    monkeypatch.setenv("BITRIX_OPS_DIALOG_ID", "951")
    seen: list[dict] = []

    def fake_call(method: str, params: dict) -> int:
        assert method == "im.message.add"
        seen.append(params)
        return 1

    monkeypatch.setattr(bitrix_send, "call_method", fake_call)
    assert bitrix_send.send_ops_dm("hello ops") == "sent"
    assert seen[0]["DIALOG_ID"] == "951"
    assert "hello ops" in seen[0]["MESSAGE"]


@pytest.mark.unit
def test_send_chat_digest_uses_tendery(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_db(monkeypatch)
    monkeypatch.setenv("BITRIX_CHAT_DIALOG_ID", "chat7543")
    seen: list[dict] = []

    def fake_call(method: str, params: dict) -> int:
        seen.append(params)
        return 1

    monkeypatch.setattr(bitrix_send, "call_method", fake_call)
    assert bitrix_send.send_chat_digest("digest body") == "sent"
    assert seen[0]["DIALOG_ID"] == "chat7543"


@pytest.mark.unit
def test_missing_bitrix_dialog_env_is_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_db(monkeypatch)
    monkeypatch.delenv("BITRIX_OPS_DIALOG_ID", raising=False)
    assert bitrix_send.send_ops_dm("hello") == "bitrix_unconfigured"


@pytest.mark.unit
def test_send_lead_keeps_lead_if_chat_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _no_db(monkeypatch)
    monkeypatch.setenv("BITRIX_SEND_CHAT", "1")
    monkeypatch.setenv("BITRIX_LEAD_SOURCE_ID", "TEST_SOURCE")
    monkeypatch.setenv("BITRIX_CHAT_DIALOG_ID", "chat7543")
    monkeypatch.setenv("BITRIX_OPS_DIALOG_ID", "951")
    dms: list[str] = []

    def fake_call(method: str, params: dict) -> object:
        if method == "crm.lead.add":
            return 8001
        raise BitrixApiError("im_down", code="bitrix_error")

    monkeypatch.setattr(bitrix_send, "call_method", fake_call)
    monkeypatch.setattr(bitrix_send, "send_ops_dm", lambda msg: dms.append(msg) or "sent")
    out = bitrix_send.send_lead_and_chat(
        {"tender_id": "rostender:1", "title": "УЗК", "effective_tier": "L1"}
    )
    assert out["lead_id"] == 8001
    assert out["chat_message_id"] is None
    assert dms and "#8001" in dms[0]

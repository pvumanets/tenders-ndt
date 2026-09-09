"""Unit: auto L1 → Bitrix leads batch (mocked REST, no SMTP)."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest

from app.bitrix import BitrixApiError, BitrixConfigError
from app.bitrix import auto_leads


class _FakeSession:
    def __init__(self, lots: dict[str, Any], states: dict[str, Any]) -> None:
        self.lots = lots
        self.states = states
        self.commits = 0

    def get(self, model: Any, key: str) -> Any:
        name = getattr(model, "__name__", "")
        if name == "Lot":
            return self.lots.get(key)
        if name == "LotState":
            return self.states.get(key)
        return None

    def refresh(self, obj: Any) -> None:
        return None

    def commit(self) -> None:
        self.commits += 1

    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(self, *_a: object) -> None:
        return None


class _FakeSessionmaker:
    def __init__(self, session: _FakeSession) -> None:
        self._session = session

    def __call__(self) -> _FakeSession:
        return self._session


def _lot(tid: str, *, price: float | None = 500_000) -> SimpleNamespace:
    return SimpleNamespace(
        tender_id=tid,
        title=f"Title {tid}",
        customer_name="ООО Тест",
        customer_inn="7700000000",
        price_rub=price,
        deadline_msk="01.01.2027",
        url="https://example.com/t",
        location="МСК",
        source_platform_id="rostender",
        tier="L1",
        fit_reason="НК",
        contact_name=None,
        contact_phone=None,
        contact_email=None,
    )


def _state(tid: str, *, tier: str = "L1", sent: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        tender_id=tid,
        ai_tier=tier,
        ai_reason_ru="ок",
        ai_reviewed_at=datetime.now(timezone.utc),
        bitrix_sent_at=datetime.now(timezone.utc) if sent else None,
    )


@pytest.mark.unit
def test_auto_l1_leads_sends_and_marks(monkeypatch: pytest.MonkeyPatch) -> None:
    tid = "rostender:qa_auto_l1"
    lot = _lot(tid)
    state = _state(tid)
    session = _FakeSession({tid: lot}, {tid: state})
    monkeypatch.setattr(auto_leads, "session_factory", lambda: _FakeSessionmaker(session))
    monkeypatch.setattr(auto_leads, "read_l1_min_price_rub", lambda _s: 100_000)
    sends: list[str] = []

    def fake_send(payload: dict) -> dict:
        sends.append(payload["tender_id"])
        return {"lead_id": 1, "chat_message_id": 2}

    monkeypatch.setattr(auto_leads, "send_lead_and_chat", fake_send)
    mail: list[object] = []
    monkeypatch.setattr("app.mail.smtp.send_mail", lambda **_k: mail.append(1) or "sent")

    counts = auto_leads.notify_auto_l1_leads([tid])
    assert counts["sent"] == 1
    assert state.bitrix_sent_at is not None
    assert session.commits == 1
    assert sends == [tid]
    assert mail == []


@pytest.mark.unit
def test_auto_l1_skips_already_sent_and_non_l1(monkeypatch: pytest.MonkeyPatch) -> None:
    a = "rostender:qa_sent"
    b = "rostender:qa_l2"
    session = _FakeSession(
        {a: _lot(a), b: _lot(b)},
        {a: _state(a, sent=True), b: _state(b, tier="L2")},
    )
    monkeypatch.setattr(auto_leads, "session_factory", lambda: _FakeSessionmaker(session))
    monkeypatch.setattr(auto_leads, "read_l1_min_price_rub", lambda _s: 100_000)
    monkeypatch.setattr(
        auto_leads,
        "send_lead_and_chat",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("should not send")),
    )
    counts = auto_leads.notify_auto_l1_leads([a, b])
    assert counts["sent"] == 0
    assert counts["skipped"] == 2


@pytest.mark.unit
def test_auto_l1_fail_continues_and_ops_dm(monkeypatch: pytest.MonkeyPatch) -> None:
    bad = "rostender:qa_bad"
    good = "rostender:qa_good"
    session = _FakeSession(
        {bad: _lot(bad), good: _lot(good)},
        {bad: _state(bad), good: _state(good)},
    )
    monkeypatch.setattr(auto_leads, "session_factory", lambda: _FakeSessionmaker(session))
    monkeypatch.setattr(auto_leads, "read_l1_min_price_rub", lambda _s: 100_000)
    dms: list[str] = []

    def fake_send(payload: dict) -> dict:
        if payload["tender_id"] == bad:
            raise BitrixApiError("boom", code="bitrix_error")
        return {"lead_id": 9, "chat_message_id": None}

    monkeypatch.setattr(auto_leads, "send_lead_and_chat", fake_send)
    monkeypatch.setattr(auto_leads, "send_ops_dm", lambda msg: dms.append(msg) or "sent")

    counts = auto_leads.notify_auto_l1_leads([bad, good])
    assert counts["failed"] == 1
    assert counts["sent"] == 1
    assert any(bad in m for m in dms)


@pytest.mark.unit
def test_auto_l1_unconfigured_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    tid = "rostender:qa_cfg"
    session = _FakeSession({tid: _lot(tid)}, {tid: _state(tid)})
    monkeypatch.setattr(auto_leads, "session_factory", lambda: _FakeSessionmaker(session))
    monkeypatch.setattr(auto_leads, "read_l1_min_price_rub", lambda _s: 100_000)
    monkeypatch.setattr(
        auto_leads,
        "send_lead_and_chat",
        lambda *_a, **_k: (_ for _ in ()).throw(BitrixConfigError("bitrix_unconfigured")),
    )
    dms: list[str] = []
    monkeypatch.setattr(auto_leads, "send_ops_dm", lambda msg: dms.append(msg) or "sent")
    counts = auto_leads.notify_auto_l1_leads([tid, "rostender:other"])
    assert counts["failed"] == 1
    assert counts["skipped"] >= 1
    assert dms

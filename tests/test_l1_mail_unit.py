"""Unit: L1 mail after auto-AI — gates, idempotency, soft SMTP fail."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from app.api.notify import notify_auto_l1
from app.db.models import Lot, LotState
from app.mail import l1_notify
from app.mail.l1_notify import build_l1_body, build_l1_subject, notify_auto_l1_lots
from app.mail import smtp as smtp_mod

_SECRET_PASS = "smtp-secret-password-qa056"
_NOW = datetime(2026, 8, 31, 7, 5, tzinfo=timezone.utc)


def _lot(**overrides: object) -> Lot:
    values: dict[str, Any] = {
        "tender_id": "rostender:qa056_l1",
        "title": "УЗК сварных соединений трубопровода",
        "url": "https://rostender.info/tender/qa056_l1",
        "customer_name": "ООО Тест Заказчик",
        "score": 7,
        "tier": "L1",
    }
    values.update(overrides)
    return Lot(**values)


def _state(**overrides: object) -> LotState:
    values: dict[str, Any] = {
        "tender_id": "rostender:qa056_l1",
        "ai_reviewed_at": _NOW,
        "ai_tier": "L1",
        "ai_reason_ru": "Услуга НК, методы ВИК/УЗК",
        "ai_trigger": "auto",
        "l1_mailed_at": None,
    }
    values.update(overrides)
    return LotState(**values)


class _FakeSession:
    def __init__(self, rows: dict[str, tuple[Lot | None, LotState | None]]) -> None:
        self._rows = rows
        self.commits = 0

    def get(self, model: type, key: str) -> Lot | LotState | None:
        lot, state = self._rows.get(key, (None, None))
        if model is Lot:
            return lot
        if model is LotState:
            return state
        return None

    def commit(self) -> None:
        self.commits += 1

    def __enter__(self) -> _FakeSession:
        return self

    def __exit__(self, *args: object) -> None:
        return None


class _FakeSessionmaker:
    def __init__(self, session: _FakeSession) -> None:
        self._session = session

    def __call__(self) -> _FakeSession:
        return self._session


def _patch_factory(monkeypatch: pytest.MonkeyPatch, session: _FakeSession) -> None:
    monkeypatch.setattr(l1_notify, "session_factory", lambda: _FakeSessionmaker(session))


@pytest.mark.unit
def test_build_l1_body_fields_no_secrets() -> None:
    subject = build_l1_subject(
        tender_id="rostender:1",
        title="УЗК " + ("длинный " * 20),
    )
    assert subject.startswith("Горячий лот L1")
    assert len(subject) < 120
    body = build_l1_body(
        tender_id="rostender:1",
        title="УЗК сварных",
        customer_name="ООО Завод",
        url="https://rostender.info/tender/1",
        ai_reason_ru="Услуга НК",
    )
    assert "УЗК сварных" in body
    assert "ООО Завод" in body
    assert "https://rostender.info/tender/1" in body
    assert "rostender:1" in body
    assert "Услуга НК" in body
    assert _SECRET_PASS not in body
    assert "SMTP_PASSWORD" not in body


@pytest.mark.unit
def test_notify_auto_l1_sends_once_and_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    lot = _lot()
    state = _state()
    session = _FakeSession({lot.tender_id: (lot, state)})
    _patch_factory(monkeypatch, session)
    monkeypatch.setenv("MAIL_L1_TO", "lead@example.test")
    monkeypatch.setenv("MAIL_L1_CC", "admin@example.test")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_PASSWORD", _SECRET_PASS)

    sent: list[dict[str, Any]] = []

    def fake_send(**kwargs: Any) -> str:
        sent.append(kwargs)
        assert _SECRET_PASS not in kwargs["subject"]
        assert _SECRET_PASS not in kwargs["body"]
        return "sent"

    monkeypatch.setattr(l1_notify, "send_mail", fake_send)

    counts = notify_auto_l1_lots([lot.tender_id])
    assert counts == {"sent": 1, "skipped": 0, "failed": 0}
    assert len(sent) == 1
    assert sent[0]["to"] == "lead@example.test"
    assert sent[0]["cc"] == "admin@example.test"
    assert "УЗК" in sent[0]["subject"]
    assert state.l1_mailed_at is not None
    assert session.commits == 1

    counts2 = notify_auto_l1_lots([lot.tender_id])
    assert counts2 == {"sent": 0, "skipped": 1, "failed": 0}
    assert len(sent) == 1


@pytest.mark.unit
def test_notify_skips_manual_rules_l2_and_no_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    cases = [
        _state(ai_trigger="manual"),
        _state(ai_tier="L2"),
        _state(ai_reviewed_at=None, ai_tier=None, ai_trigger=None),
    ]
    monkeypatch.setenv("MAIL_L1_TO", "lead@example.test")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    calls: list[str] = []
    monkeypatch.setattr(
        l1_notify,
        "send_mail",
        lambda **_k: calls.append("sent") or "sent",
    )

    for idx, state in enumerate(cases):
        tid = f"rostender:skip_{idx}"
        lot = _lot(tender_id=tid, tier="L1")
        state.tender_id = tid
        session = _FakeSession({tid: (lot, state)})
        _patch_factory(monkeypatch, session)
        counts = notify_auto_l1_lots([tid])
        assert counts["sent"] == 0
        assert counts["skipped"] == 1
        assert state.l1_mailed_at is None

    assert calls == []


@pytest.mark.unit
def test_notify_smtp_unconfigured_leaves_mailed_null(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    lot = _lot()
    state = _state()
    session = _FakeSession({lot.tender_id: (lot, state)})
    _patch_factory(monkeypatch, session)
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_RELAY_URL", raising=False)
    monkeypatch.delenv("SMTP_RELAY_SECRET", raising=False)
    monkeypatch.setenv("MAIL_L1_TO", "lead@example.test")

    with caplog.at_level("INFO"):
        counts = notify_auto_l1_lots([lot.tender_id])

    assert counts["sent"] == 0
    assert counts["skipped"] >= 1
    assert state.l1_mailed_at is None
    assert session.commits == 0
    assert any("smtp_unconfigured" in r.message for r in caplog.records)
    assert smtp_mod.l1_mail_configured() is False


@pytest.mark.unit
def test_notify_smtp_failed_no_mailed_at(monkeypatch: pytest.MonkeyPatch) -> None:
    lot = _lot()
    state = _state()
    session = _FakeSession({lot.tender_id: (lot, state)})
    _patch_factory(monkeypatch, session)
    monkeypatch.setenv("MAIL_L1_TO", "lead@example.test")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(l1_notify, "send_mail", lambda **_k: "smtp_failed")

    counts = notify_auto_l1_lots([lot.tender_id])
    assert counts == {"sent": 0, "skipped": 0, "failed": 1}
    assert state.l1_mailed_at is None
    assert session.commits == 0


@pytest.mark.unit
def test_notify_auto_l1_empty_and_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[list[str]] = []

    def fake_lots(ids: list[str]) -> dict[str, int]:
        called.append(ids)
        return {"sent": 0, "skipped": 0, "failed": 0}

    monkeypatch.setattr("app.api.notify.notify_auto_l1_lots", fake_lots)
    notify_auto_l1([])
    assert called == []
    notify_auto_l1(["rostender:qa_l1"])
    assert called == [["rostender:qa_l1"]]

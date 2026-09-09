"""Unit: notify digest + ops session → Bitrix, not SMTP."""
from __future__ import annotations

import pytest

from app.api import notify


@pytest.mark.unit
def test_build_run_digest_message_shape() -> None:
    text = notify.build_run_digest_message(
        report={"new": 3, "updated": 1, "already": 5, "expired": 2},
        ai_processed=4,
        ai_failed=1,
        leads_sent=2,
        next_fire_at="2026-09-10T09:00:00+03:00",
    )
    assert "Разведчик · авторазбор" in text
    assert "Новых лотов: 3" in text
    assert "ИИ разобрал: 4" in text
    assert "сбоев: 1" in text
    assert "L1 → лиды Битрикс: 2" in text
    assert "Следующий слот:" in text
    assert "Scout" not in text


@pytest.mark.unit
def test_notify_run_digest_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def fake(msg: str) -> str:
        seen.append(msg)
        return "sent"

    monkeypatch.setattr(notify, "send_chat_digest", fake)
    status = notify.notify_run_digest(
        report={"new": 1},
        ai_processed=1,
        ai_failed=0,
        leads_sent=1,
        next_fire_at=None,
    )
    assert status == "sent"
    assert "Разведчик" in seen[0]


@pytest.mark.unit
def test_notify_ops_session_dm_not_smtp(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def fake(msg: str) -> str:
        seen.append(msg)
        return "sent"

    monkeypatch.setattr(notify, "send_ops_dm", fake)
    mail_calls: list[object] = []

    def no_mail(*_a, **_k):
        mail_calls.append(1)
        return "sent"

    monkeypatch.setattr("app.mail.smtp.send_ops_mail", no_mail)
    assert notify.notify_ops_session(platform_id="rostender", session="expired") == "sent"
    assert notify.notify_ops_session(platform_id="b2b-center", session="blocked") == "sent"
    assert notify.notify_ops_session(platform_id="x", session="ok") == "skipped"
    assert mail_calls == []
    assert all("Разведчик" in m for m in seen)
    assert all("Scout" not in m for m in seen)


@pytest.mark.unit
def test_notify_auto_l1_delegates_to_bitrix(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []

    def fake(ids: list[str]) -> dict[str, int]:
        seen.append(ids)
        return {"sent": 1, "skipped": 0, "failed": 0}

    monkeypatch.setattr(notify, "notify_auto_l1_leads", fake)
    notify.notify_auto_l1([])
    notify.notify_auto_l1(["rostender:qa_l1"])
    assert seen == [["rostender:qa_l1"]]

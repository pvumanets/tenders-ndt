"""Unit: SMTP port 465 uses SSL; 587 uses STARTTLS."""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.mail import smtp as smtp_mod

_FAKE_PASS = "smtp-secret-password-qa060"


class _SmtpCtx:
    def __init__(self, client: MagicMock) -> None:
        self.client = client

    def __enter__(self) -> MagicMock:
        return self.client

    def __exit__(self, *args: object) -> None:
        return None


def _patch_env(monkeypatch: pytest.MonkeyPatch, *, port: str) -> None:
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_PORT", port)
    monkeypatch.setenv("SMTP_USER", "sender@example.test")
    monkeypatch.setenv("SMTP_PASSWORD", _FAKE_PASS)
    monkeypatch.setenv("SMTP_FROM", "Sender <sender@example.test>")
    monkeypatch.setenv("SMTP_TLS", "1")


def test_send_mail_port_465_uses_smtp_ssl(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_env(monkeypatch, port="465")
    client = MagicMock()
    calls: list[tuple[Any, ...]] = []

    def fake_ssl(*args: Any, **kwargs: Any) -> _SmtpCtx:
        calls.append(("SSL", args, kwargs))
        return _SmtpCtx(client)

    def boom_smtp(*_a: Any, **_k: Any) -> None:
        raise AssertionError("SMTP must not be used on port 465")

    monkeypatch.setattr(smtp_mod.smtplib, "SMTP_SSL", fake_ssl)
    monkeypatch.setattr(smtp_mod.smtplib, "SMTP", boom_smtp)

    status = smtp_mod.send_mail(to="to@example.test", subject="t", body="b")
    assert status == "sent"
    assert len(calls) == 1
    assert calls[0][0] == "SSL"
    assert calls[0][1][:2] == ("smtp.example.test", 465)
    client.login.assert_called_once_with("sender@example.test", _FAKE_PASS)
    client.send_message.assert_called_once()
    client.starttls.assert_not_called()


def test_send_mail_port_587_uses_starttls(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_env(monkeypatch, port="587")
    client = MagicMock()
    calls: list[tuple[Any, ...]] = []

    def fake_smtp(*args: Any, **kwargs: Any) -> _SmtpCtx:
        calls.append(("SMTP", args, kwargs))
        return _SmtpCtx(client)

    def boom_ssl(*_a: Any, **_k: Any) -> None:
        raise AssertionError("SMTP_SSL must not be used on port 587")

    monkeypatch.setattr(smtp_mod.smtplib, "SMTP", fake_smtp)
    monkeypatch.setattr(smtp_mod.smtplib, "SMTP_SSL", boom_ssl)

    status = smtp_mod.send_mail(to="to@example.test", subject="t", body="b")
    assert status == "sent"
    assert len(calls) == 1
    assert calls[0][0] == "SMTP"
    assert calls[0][1][:2] == ("smtp.example.test", 587)
    client.starttls.assert_called_once()
    client.login.assert_called_once_with("sender@example.test", _FAKE_PASS)
    client.send_message.assert_called_once()

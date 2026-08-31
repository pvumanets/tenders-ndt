"""Thin SMTP send for ops alerts. Values only from env; never log secrets."""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

log = logging.getLogger("uvicorn.error")


def smtp_configured() -> bool:
    host = (os.getenv("SMTP_HOST") or "").strip()
    mail_to = (os.getenv("MAIL_OPS_TO") or "").strip()
    return bool(host and mail_to)


def send_ops_mail(*, subject: str, body: str) -> str:
    """
    Send ops alert. Returns 'sent' | 'smtp_unconfigured' | 'smtp_failed'.
    Does not raise. Never include cookie values / jar / passwords in subject/body.
    """
    host = (os.getenv("SMTP_HOST") or "").strip()
    mail_to = (os.getenv("MAIL_OPS_TO") or "").strip()
    if not host or not mail_to:
        log.info("smtp_unconfigured")
        return "smtp_unconfigured"

    port_raw = (os.getenv("SMTP_PORT") or "587").strip()
    try:
        port = int(port_raw)
    except ValueError:
        port = 587
    user = (os.getenv("SMTP_USER") or "").strip()
    password = os.getenv("SMTP_PASSWORD") or ""
    mail_from = (os.getenv("SMTP_FROM") or user or mail_to).strip()
    use_tls = (os.getenv("SMTP_TLS") or "1").strip().lower() in {"1", "true", "yes"}

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            if use_tls:
                smtp.starttls()
            if user:
                smtp.login(user, password)
            smtp.send_message(msg)
        return "sent"
    except Exception as exc:  # noqa: BLE001
        log.warning("smtp_failed: %s", type(exc).__name__)
        return "smtp_failed"

"""Thin SMTP send. Values only from env; never log secrets."""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

log = logging.getLogger("uvicorn.error")


def smtp_host_configured() -> bool:
    return bool((os.getenv("SMTP_HOST") or "").strip())


def smtp_configured() -> bool:
    """Ops alert configured (host + MAIL_OPS_TO)."""
    host = (os.getenv("SMTP_HOST") or "").strip()
    mail_to = (os.getenv("MAIL_OPS_TO") or "").strip()
    return bool(host and mail_to)


def l1_mail_configured() -> bool:
    host = (os.getenv("SMTP_HOST") or "").strip()
    mail_to = (os.getenv("MAIL_L1_TO") or "").strip()
    return bool(host and mail_to)


def send_mail(
    *,
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
) -> str:
    """
    Send one message. Returns 'sent' | 'smtp_unconfigured' | 'smtp_failed'.
    Does not raise. Never include cookie values / jar / passwords in subject/body.
    """
    host = (os.getenv("SMTP_HOST") or "").strip()
    to_addr = (to or "").strip()
    if not host or not to_addr:
        log.info("smtp_unconfigured")
        return "smtp_unconfigured"

    port_raw = (os.getenv("SMTP_PORT") or "587").strip()
    try:
        port = int(port_raw)
    except ValueError:
        port = 587
    user = (os.getenv("SMTP_USER") or "").strip()
    password = os.getenv("SMTP_PASSWORD") or ""
    mail_from = (os.getenv("SMTP_FROM") or user or to_addr).strip()
    use_tls = (os.getenv("SMTP_TLS") or "1").strip().lower() in {"1", "true", "yes"}
    cc_addr = (cc or "").strip() or None

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = to_addr
    if cc_addr:
        msg["Cc"] = cc_addr
    msg.set_content(body)

    recipients = [to_addr]
    if cc_addr:
        recipients.append(cc_addr)

    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            if use_tls:
                smtp.starttls()
            if user:
                smtp.login(user, password)
            smtp.send_message(msg, to_addrs=recipients)
        return "sent"
    except Exception as exc:  # noqa: BLE001
        log.warning("smtp_failed: %s", type(exc).__name__)
        return "smtp_failed"


def send_ops_mail(*, subject: str, body: str) -> str:
    """Ops alert to MAIL_OPS_TO."""
    mail_to = (os.getenv("MAIL_OPS_TO") or "").strip()
    return send_mail(to=mail_to, subject=subject, body=body)

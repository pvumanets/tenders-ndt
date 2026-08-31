"""Thin SMTP send. Values only from env; never log secrets.

Direct SMTP (nic.ru) or HTTP relay (SMTP_RELAY_URL) when VPS cannot reach mail host.
"""
from __future__ import annotations

import json
import logging
import os
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

log = logging.getLogger("uvicorn.error")


def smtp_host_configured() -> bool:
    return bool((os.getenv("SMTP_HOST") or "").strip())


def relay_configured() -> bool:
    url = (os.getenv("SMTP_RELAY_URL") or "").strip()
    secret = (os.getenv("SMTP_RELAY_SECRET") or "").strip()
    return bool(url and secret)


def smtp_configured() -> bool:
    """Ops alert configured (relay or host + MAIL_OPS_TO)."""
    mail_to = (os.getenv("MAIL_OPS_TO") or "").strip()
    return bool(mail_to and (relay_configured() or smtp_host_configured()))


def l1_mail_configured() -> bool:
    mail_to = (os.getenv("MAIL_L1_TO") or "").strip()
    return bool(mail_to and (relay_configured() or smtp_host_configured()))


def _send_via_relay(
    *,
    to: str,
    subject: str,
    body: str,
    cc: str | None,
) -> str:
    base = (os.getenv("SMTP_RELAY_URL") or "").strip().rstrip("/")
    secret = (os.getenv("SMTP_RELAY_SECRET") or "").strip()
    url = f"{base}/send"
    payload = json.dumps(
        {"to": to, "subject": subject, "body": body, "cc": cc or None}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {secret}",
            "User-Agent": "ndt-tender-scout-mail",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
            if data.get("ok"):
                return "sent"
            log.warning("smtp_relay_failed: bad_payload")
            return "smtp_failed"
    except urllib.error.HTTPError as exc:
        log.warning("smtp_relay_failed: HTTPError_%s", exc.code)
        return "smtp_failed"
    except Exception as exc:  # noqa: BLE001
        log.warning("smtp_relay_failed: %s", type(exc).__name__)
        return "smtp_failed"


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
    Prefers SMTP_RELAY_URL when set; else direct SMTP (465=SSL, else STARTTLS).
    """
    to_addr = (to or "").strip()
    if not to_addr:
        log.info("smtp_unconfigured")
        return "smtp_unconfigured"

    if relay_configured():
        return _send_via_relay(to=to_addr, subject=subject, body=body, cc=cc)

    host = (os.getenv("SMTP_HOST") or "").strip()
    if not host:
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
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg, to_addrs=recipients)
        else:
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

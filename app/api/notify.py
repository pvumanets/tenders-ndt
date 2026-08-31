"""Outbound notifications. L1 sales mail lands in 056; ops session alerts in 055."""
from __future__ import annotations

import logging

from app.mail.smtp import send_ops_mail

log = logging.getLogger("uvicorn.error")


def notify_auto_l1(tender_ids: list[str]) -> None:
    """054 stub: do not send mail. 056 implements SMTP. Never log secrets or cookie values."""
    if not tender_ids:
        return
    log.info("notify_auto_l1 stub: %s lot(s) — SMTP in 056", len(tender_ids))


def notify_ops_session(*, platform_id: str, session: str) -> str:
    """
    Soft ops alert when platform session is bad after upload or runner skip.
    Returns send_ops_mail status. Never raises; never logs cookie values.
    """
    code = str(session or "unknown")
    if code not in {"expired", "missing", "missing_cookies"}:
        return "skipped"
    api_session = "missing" if code in {"missing", "missing_cookies"} else code
    subject = f"Scout: сессия {platform_id} — {api_session}"
    body = (
        f"Площадка: {platform_id}\n"
        f"Статус сессии: {api_session}\n"
        f"Обновите cookies в Настройках (JSON), без SSH.\n"
    )
    return send_ops_mail(subject=subject, body=body)

"""L1 mail after auto-AI. SMTP body lands in 056 — this is a no-op hook."""
from __future__ import annotations

import logging

log = logging.getLogger("uvicorn.error")


def notify_auto_l1(tender_ids: list[str]) -> None:
    """054 stub: do not send mail. 056 implements SMTP. Never log secrets or cookie values."""
    if not tender_ids:
        return
    log.info("notify_auto_l1 stub: %s lot(s) — SMTP in 056", len(tender_ids))

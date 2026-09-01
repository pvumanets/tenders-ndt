"""L1 sales mail after auto-AI. One message per lot; never log secrets."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from app.api.operator_settings import read_l1_min_price_rub
from app.db.models import Lot, LotState
from app.db.session import session_factory
from app.mail.smtp import send_mail
from app.worker.customer_name import clean_customer_name

log = logging.getLogger("uvicorn.error")

_REASON_MAX = 400
_TITLE_MAX = 80


def _price_ok(lot: Lot, min_price: int) -> bool:
    if lot.price_rub is None:
        return True
    return int(lot.price_rub) >= min_price


def _eligible(state: LotState | None, lot: Lot, min_price: int) -> bool:
    if state is None:
        return False
    if state.ai_trigger != "auto":
        return False
    if state.ai_reviewed_at is None:
        return False
    if state.ai_tier != "L1":
        return False
    if state.l1_mailed_at is not None:
        return False
    if not _price_ok(lot, min_price):
        return False
    return True


def build_l1_subject(*, tender_id: str, title: str) -> str:
    short = (title or "").strip() or tender_id
    if len(short) > _TITLE_MAX:
        short = short[: _TITLE_MAX - 1] + "…"
    return f"Горячий лот L1 · {short}"


def build_l1_body(
    *,
    tender_id: str,
    title: str,
    customer_name: str | None,
    url: str | None,
    ai_reason_ru: str | None,
) -> str:
    reason = (ai_reason_ru or "").strip()
    if len(reason) > _REASON_MAX:
        reason = reason[: _REASON_MAX - 1] + "…"
    customer = clean_customer_name(customer_name) or "—"
    link = (url or "").strip() or "—"
    lines = [
        f"Название: {(title or '').strip() or '—'}",
        f"Заказчик: {customer}",
        f"Ссылка: {link}",
        f"ID: {tender_id}",
        f"Оценка ИИ: {reason or '—'}",
    ]
    return "\n".join(lines) + "\n"


def notify_auto_l1_lots(tender_ids: list[str]) -> dict[str, int]:
    """
    Send L1 sales mail for eligible lots. Soft-fail SMTP.
    Returns counts: sent / skipped / failed. Never raises.
    """
    counts = {"sent": 0, "skipped": 0, "failed": 0}
    if not tender_ids:
        return counts

    mail_to = (os.getenv("MAIL_L1_TO") or "").strip()
    mail_cc = (os.getenv("MAIL_L1_CC") or "").strip() or None

    try:
        factory = session_factory()
    except RuntimeError:
        log.info("notify_auto_l1: database_unconfigured — skip")
        counts["skipped"] = len(tender_ids)
        return counts

    seen: set[str] = set()
    with factory() as session:
        min_price = read_l1_min_price_rub(session)
        for raw_id in tender_ids:
            tender_id = str(raw_id or "").strip()
            if not tender_id or tender_id in seen:
                counts["skipped"] += 1
                continue
            seen.add(tender_id)

            lot = session.get(Lot, tender_id)
            state = session.get(LotState, tender_id)
            if lot is None or not _eligible(state, lot, min_price):
                counts["skipped"] += 1
                continue
            assert state is not None

            subject = build_l1_subject(tender_id=tender_id, title=lot.title or "")
            body = build_l1_body(
                tender_id=tender_id,
                title=lot.title or "",
                customer_name=lot.customer_name,
                url=lot.url,
                ai_reason_ru=state.ai_reason_ru,
            )
            status = send_mail(to=mail_to, cc=mail_cc, subject=subject, body=body)
            if status == "sent":
                state.l1_mailed_at = datetime.now(timezone.utc)
                session.commit()
                counts["sent"] += 1
            elif status == "smtp_unconfigured":
                counts["skipped"] += 1
                # No further sends will work; remaining lots also skip without hammering.
                remaining = [
                    tid
                    for tid in tender_ids
                    if str(tid or "").strip() and str(tid).strip() not in seen
                ]
                counts["skipped"] += len(remaining)
                break
            else:
                counts["failed"] += 1

    if counts["sent"]:
        log.info("notify_auto_l1: sent=%s skipped=%s failed=%s", counts["sent"], counts["skipped"], counts["failed"])
    elif counts["failed"]:
        log.warning("notify_auto_l1: sent=0 skipped=%s failed=%s", counts["skipped"], counts["failed"])
    return counts

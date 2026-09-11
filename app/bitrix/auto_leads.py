"""After AI: create Bitrix leads for new L1 lots. Soft-fail; no SMTP."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.api.operator_settings import read_l1_min_price_rub
from app.bitrix import BitrixApiError, BitrixConfigError
from app.bitrix.send import send_lead_and_chat, send_ops_dm
from app.db.models import Lot, LotState
from app.db.session import session_factory

log = logging.getLogger("uvicorn.error")


def _price_ok(lot: Lot, min_price: int) -> bool:
    if lot.price_rub is None:
        return True
    return int(lot.price_rub) >= min_price


def _eligible(state: LotState | None, lot: Lot, min_price: int) -> bool:
    if state is None:
        return False
    if state.ai_reviewed_at is None:
        return False
    if state.ai_tier != "L1":
        return False
    if state.bitrix_sent_at is not None:
        return False
    if not _price_ok(lot, min_price):
        return False
    return True


def _lot_payload(lot: Lot, state: LotState) -> dict[str, Any]:
    return {
        "tender_id": lot.tender_id,
        "title": lot.title,
        "customer_name": lot.customer_name,
        "customer_inn": lot.customer_inn,
        "price_rub": float(lot.price_rub) if lot.price_rub is not None else None,
        "deadline_msk": lot.deadline_msk,
        "url": lot.url,
        "location": lot.location,
        "source_platform_id": lot.source_platform_id,
        "tier": lot.tier,
        "fit_reason": lot.fit_reason,
        "contact_name": lot.contact_name,
        "contact_phone": lot.contact_phone,
        "contact_email": lot.contact_email,
        "effective_tier": state.ai_tier or lot.tier,
        "ai_tier": state.ai_tier,
        "ai_reason_ru": state.ai_reason_ru,
    }


def notify_auto_l1_leads(tender_ids: list[str]) -> dict[str, int]:
    """
    Create Bitrix lead (+ chat) for eligible AI-L1 lots.
    Soft-fail per lot; ops DM on failure. Never raises. No SMTP.
    """
    counts = {"sent": 0, "skipped": 0, "failed": 0}
    if not tender_ids:
        return counts

    from app.api.operator_settings import resolve_bitrix_auto_l1_enabled

    if not resolve_bitrix_auto_l1_enabled():
        log.info("notify_auto_l1_leads: auto_l1 disabled — skip")
        counts["skipped"] = len(tender_ids)
        return counts

    try:
        factory = session_factory()
    except RuntimeError:
        log.info("notify_auto_l1_leads: database_unconfigured — skip")
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

            session.refresh(state)
            if state.bitrix_sent_at is not None:
                counts["skipped"] += 1
                continue

            payload = _lot_payload(lot, state)
            try:
                send_lead_and_chat(payload)
            except BitrixConfigError:
                log.info("notify_auto_l1_leads: bitrix_unconfigured — stop batch")
                send_ops_dm(
                    "Разведчик: Битрикс не настроен (нет вебхука). "
                    f"Автолид L1 не создан: {tender_id}"
                )
                remaining = [
                    tid
                    for tid in tender_ids
                    if str(tid or "").strip() and str(tid).strip() not in seen
                ]
                counts["failed"] += 1
                counts["skipped"] += len(remaining)
                break
            except BitrixApiError as exc:
                counts["failed"] += 1
                send_ops_dm(
                    "Разведчик: не удалось создать лид L1.\n"
                    f"ID: {tender_id}\n"
                    f"Код: {exc.code}"
                )
                continue
            except Exception as exc:  # noqa: BLE001
                counts["failed"] += 1
                send_ops_dm(
                    "Разведчик: сбой автолида L1.\n"
                    f"ID: {tender_id}\n"
                    f"Ошибка: {type(exc).__name__}"
                )
                continue

            state.bitrix_sent_at = datetime.now(timezone.utc)
            session.commit()
            counts["sent"] += 1

    if counts["sent"]:
        log.info(
            "notify_auto_l1_leads: sent=%s skipped=%s failed=%s",
            counts["sent"],
            counts["skipped"],
            counts["failed"],
        )
    elif counts["failed"]:
        log.warning(
            "notify_auto_l1_leads: sent=0 skipped=%s failed=%s",
            counts["skipped"],
            counts["failed"],
        )
    return counts

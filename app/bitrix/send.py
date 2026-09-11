"""Send lot → Bitrix lead (+ chat «Тендеры»); ops DM; run digest."""
from __future__ import annotations

import logging
from typing import Any

from app.bitrix import (
    BitrixApiError,
    BitrixConfigError,
    call_method,
    chat_dialog_id,
    ops_dialog_id,
)
from app.bitrix.fields import build_chat_message, build_lead_fields, lead_fields_to_params

log = logging.getLogger("uvicorn.error")


def chat_send_enabled() -> bool:
    """Lead ping to sales chat. Default on. DB override > BITRIX_SEND_CHAT env."""
    from app.api.operator_settings import resolve_bitrix_send_chat

    return resolve_bitrix_send_chat()


def send_lead_and_chat(lot: dict[str, Any]) -> dict[str, Any]:
    """
    Create CRM lead; chat when send-chat toggle enabled (default on).
    Lead success is authoritative: chat failure does not raise (ops DM + null chat id).
    Raises BitrixConfigError / BitrixApiError only if lead add fails.
    Returns { lead_id, chat_message_id | null }.
    """
    fields = build_lead_fields(lot)
    params = lead_fields_to_params(fields)
    lead_id = call_method("crm.lead.add", params)
    if lead_id is None:
        raise BitrixApiError("empty_lead_id", code="bitrix_error")
    chat_id = None
    if chat_send_enabled():
        msg = build_chat_message(lot=lot, lead_id=lead_id)
        try:
            chat_id = call_method(
                "im.message.add",
                {"DIALOG_ID": chat_dialog_id(), "MESSAGE": msg},
            )
        except BitrixApiError as exc:
            log.warning("bitrix_chat_after_lead failed lead_id=%s code=%s", lead_id, exc.code)
            send_ops_dm(
                "Разведчик: лид создан, чат «Тендеры» не отправился.\n"
                f"Лид CRM: #{lead_id}\n"
                f"Код: {exc.code}"
            )
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "bitrix_chat_after_lead unexpected lead_id=%s err=%s",
                lead_id,
                type(exc).__name__,
            )
            send_ops_dm(
                "Разведчик: лид создан, чат «Тендеры» сбой.\n"
                f"Лид CRM: #{lead_id}\n"
                f"Ошибка: {type(exc).__name__}"
            )
    return {"lead_id": lead_id, "chat_message_id": chat_id}


def send_im(*, dialog_id: str, message: str) -> Any:
    """Low-level IM send. Raises on config/API errors."""
    text = (message or "").strip()
    if not text:
        raise BitrixApiError("empty_message", code="bitrix_error")
    return call_method(
        "im.message.add",
        {"DIALOG_ID": str(dialog_id).strip(), "MESSAGE": text},
    )


def send_ops_dm(message: str) -> str:
    """
    Soft ops alert to owner DM (ops dialog id).
    Returns sent | bitrix_unconfigured | bitrix_failed | skipped. Never raises.
    """
    from app.api.operator_settings import resolve_bitrix_ops_alerts_enabled

    if not resolve_bitrix_ops_alerts_enabled():
        log.info("bitrix_ops_dm: alerts disabled — skip")
        return "skipped"
    try:
        send_im(dialog_id=ops_dialog_id(), message=message)
        return "sent"
    except BitrixConfigError:
        log.info("bitrix_ops_dm: unconfigured — skip")
        return "bitrix_unconfigured"
    except BitrixApiError as exc:
        log.warning("bitrix_ops_dm: failed code=%s", exc.code)
        return "bitrix_failed"
    except Exception as exc:  # noqa: BLE001
        log.warning("bitrix_ops_dm: unexpected %s", type(exc).__name__)
        return "bitrix_failed"


def send_chat_digest(message: str) -> str:
    """Soft digest to «Тендеры». Never raises. Never uses ops DM."""
    try:
        send_im(dialog_id=chat_dialog_id(), message=message)
        return "sent"
    except BitrixConfigError:
        log.info("bitrix_digest: unconfigured — skip")
        return "bitrix_unconfigured"
    except BitrixApiError as exc:
        log.warning("bitrix_digest: failed code=%s", exc.code)
        return "bitrix_failed"
    except Exception as exc:  # noqa: BLE001
        log.warning("bitrix_digest: unexpected %s", type(exc).__name__)
        return "bitrix_failed"

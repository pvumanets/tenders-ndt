"""Send Scout lot → Bitrix lead (+ optional chat «Тендеры»)."""
from __future__ import annotations

import os
from typing import Any

from app.bitrix import BitrixApiError, BitrixConfigError, call_method, chat_dialog_id
from app.bitrix.fields import build_chat_message, build_lead_fields, lead_fields_to_params


def chat_send_enabled() -> bool:
    """Owner lock: no chat spam until form/fields look right. Opt-in via env."""
    return (os.getenv("BITRIX_SEND_CHAT") or "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def send_lead_and_chat(lot: dict[str, Any]) -> dict[str, Any]:
    """
    Create CRM lead; chat only if BITRIX_SEND_CHAT=1.
    Raises BitrixConfigError / BitrixApiError.
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
        chat_id = call_method(
            "im.message.add",
            {"DIALOG_ID": chat_dialog_id(), "MESSAGE": msg},
        )
    return {"lead_id": lead_id, "chat_message_id": chat_id}

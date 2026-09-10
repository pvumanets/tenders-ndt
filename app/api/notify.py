"""Outbound notifications: Bitrix leads / chat / ops DM. SMTP call sites retired."""
from __future__ import annotations

import logging
from typing import Any

from app.bitrix.auto_leads import notify_auto_l1_leads
from app.bitrix.send import send_chat_digest, send_ops_dm

log = logging.getLogger("uvicorn.error")

_OPS_SESSION_CODES = frozenset(
    {"expired", "missing", "missing_cookies", "blocked"}
)


def notify_auto_l1(tender_ids: list[str]) -> None:
    """
    After AI: Bitrix lead (+ chat) for eligible L1 lots.
    Soft-fail; never abort pipeline. Never SMTP. Never log secrets.
    """
    if not tender_ids:
        return
    notify_auto_l1_leads(tender_ids)


def notify_ops_session(*, platform_id: str, session: str) -> str:
    """
    Soft ops alert to owner DM when platform session is bad.
    Returns send status. Never raises; never logs cookie values. No SMTP.
    """
    code = str(session or "unknown")
    if code not in _OPS_SESSION_CODES:
        return "skipped"
    api_session = "missing" if code in {"missing", "missing_cookies"} else code
    message = (
        f"[b]Разведчик · сессия[/b]\n"
        f"Площадка: {platform_id}\n"
        f"Статус: {api_session}\n"
        f"Обновите cookies в Настройках (JSON)."
    )
    return send_ops_dm(message)


def notify_ops_event(*, subject: str, body: str) -> str:
    """Soft ops DM for run/AI/lead failures. Never raises. No SMTP."""
    title = (subject or "событие").strip() or "событие"
    text = (body or "").strip()
    message = f"[b]Разведчик · {title}[/b]"
    if text:
        message = f"{message}\n{text}"
    return send_ops_dm(message)


def build_run_digest_message(
    *,
    report: dict[str, Any] | None,
    ai_processed: int,
    ai_failed: int,
    leads_sent: int,
    next_fire_at: str | None,
) -> str:
    """BBCode digest for chat «Тендеры». No secrets."""
    rep = report or {}
    new_n = int(rep.get("new") or 0)
    upd_n = int(rep.get("updated") or 0)
    already_n = int(rep.get("already") or 0)
    expired_n = int(rep.get("expired") or 0)
    lines = [
        "[b]Разведчик · авторазбор[/b]",
        "--------------------",
        f"Новых лотов: {new_n}",
        f"Обновлено: {upd_n}",
        f"Без изменений: {already_n}",
        f"В просроченные: {expired_n}",
        f"ИИ разобрал: {ai_processed}"
        + (f" (сбоев: {ai_failed})" if ai_failed else ""),
        f"L1 → лиды Битрикс: {leads_sent}",
    ]
    nxt = (next_fire_at or "").strip()
    if nxt:
        lines.append(f"Следующий слот: {nxt}")
    lines.append("[i]Сводка отправлена автоматически из Разведчика.[/i]")
    return "\n".join(lines)


def notify_run_digest(
    *,
    report: dict[str, Any] | None,
    ai_processed: int,
    ai_failed: int,
    leads_sent: int,
    next_fire_at: str | None,
) -> str:
    """Soft digest to «Тендеры». Never raises."""
    msg = build_run_digest_message(
        report=report,
        ai_processed=ai_processed,
        ai_failed=ai_failed,
        leads_sent=leads_sent,
        next_fire_at=next_fire_at,
    )
    return send_chat_digest(msg)

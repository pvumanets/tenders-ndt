"""Inbox CSV / XLSX export (story 100)."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from openpyxl import Workbook
from sqlalchemy import func, select

from app.api.inbox import InboxQueryError, list_inbox
from app.db.models import Document
from app.db.session import session_factory

MSK = ZoneInfo("Europe/Moscow")

EXPORT_COLUMN_HEADERS: dict[str, str] = {
    "tender_id": "Id",
    "title": "Название",
    "customer_name": "Заказчик",
    "customer_inn": "ИНН",
    "location": "Регион",
    "status": "Статус",
    "url": "Ссылка",
    "source_platform_id": "Площадка",
    "price_rub": "НМЦ, ₽",
    "deadline_msk": "Срок подачи",
    "published_msk": "Опубликовано",
    "ingested_at": "Попало к нам",
    "deadline_expired": "Срок истёк",
    "score": "Балл",
    "fit_reason": "Почему подходит",
    "rules_tier": "Тир по правилам",
    "ai_tier": "Тир ИИ",
    "manual_tier": "Тир вручную",
    "effective_tier": "Итоговый тир",
    "ai_reviewed": "Разобрано ИИ",
    "ai_trigger": "Источник ИИ",
    "ai_reason_ru": "Почему ИИ",
    "ai_error": "Ошибка ИИ",
    "ai_wrong": "ИИ ошибся",
    "ai_wrong_note": "Заметка об ошибке ИИ",
    "viewed": "Просмотрено",
    "board_hidden": "Скрыт с доски",
    "bitrix_sent_at": "В Битрикс",
    "contact_name": "Контакт",
    "contact_phone": "Телефон",
    "contact_email": "Email",
    "documents_count": "Число файлов",
}

EXPORT_COLUMN_KEYS = frozenset(EXPORT_COLUMN_HEADERS)
AI_REVIEW_PRESET: tuple[str, ...] = (
    "tender_id",
    "title",
    "customer_name",
    "rules_tier",
    "ai_tier",
    "manual_tier",
    "effective_tier",
    "ai_reason_ru",
    "ai_error",
    "ai_wrong",
    "ai_wrong_note",
    "ai_trigger",
    "score",
    "fit_reason",
    "url",
    "source_platform_id",
)
BOOL_COLUMNS = frozenset(
    {"deadline_expired", "ai_reviewed", "ai_wrong", "viewed", "board_hidden"}
)
DATE_COLUMNS = frozenset(
    {"deadline_msk", "published_msk", "ingested_at", "bitrix_sent_at"}
)
_FORMULA_PREFIX = frozenset("=+-@")


def _filter_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).strip()
    return text if text else None


def parse_export_body(body: Any) -> tuple[str, list[str], dict[str, Any]]:
    if body is None:
        body = {}
    if not isinstance(body, dict):
        raise InboxQueryError("invalid_body")
    fmt = str(body.get("format") or "").strip().lower()
    if fmt not in {"csv", "xlsx"}:
        raise InboxQueryError("invalid_format")
    raw_cols = body.get("columns")
    if not isinstance(raw_cols, list) or not raw_cols:
        raise InboxQueryError("invalid_columns")
    columns: list[str] = []
    seen: set[str] = set()
    for item in raw_cols:
        if not isinstance(item, str):
            raise InboxQueryError("invalid_columns")
        key = item.strip()
        if key not in EXPORT_COLUMN_KEYS:
            raise InboxQueryError("invalid_columns")
        if key in seen:
            continue
        seen.add(key)
        columns.append(key)
    if not columns:
        raise InboxQueryError("invalid_columns")

    filters: dict[str, Any] = {
        "unread": _filter_str(body.get("unread")),
        "tier": _filter_str(body.get("tier")) or "fit",
        "q": str(body.get("q") or ""),
        "deadline_from": _filter_str(body.get("deadline_from")),
        "deadline_to": _filter_str(body.get("deadline_to")),
        "ingested_from": _filter_str(body.get("ingested_from")),
        "ingested_to": _filter_str(body.get("ingested_to")),
        "ai_reviewed": _filter_str(body.get("ai_reviewed")),
        "ai_trigger": _filter_str(body.get("ai_trigger")),
        "ai_error": body.get("ai_error"),
        "ai_wrong": body.get("ai_wrong"),
        "price_min_rub": _filter_str(body.get("price_min_rub")),
        "platform": _filter_str(body.get("platform")),
        "bitrix": _filter_str(body.get("bitrix")),
        "sort": _filter_str(body.get("sort")),
    }
    return fmt, columns, filters


def escape_formula_cell(value: str) -> str:
    if value and value[0] in _FORMULA_PREFIX:
        return "'" + value
    return value


def _as_date_cell(value: Any) -> str:
    if value is None or value == "":
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text and len(text) > 10:
        # deadline_msk may be "20.08.2026 15:00" or ISO date already
        head = text.split(" ", 1)[0]
        if len(head) == 10 and head[4] == "-":
            return head
        # DD.MM.YYYY → YYYY-MM-DD
        parts = head.split(".")
        if len(parts) == 3 and len(parts[2]) == 4:
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
        return head
    if len(text) >= 10 and text[4] == "-":
        return text[:10]
    parts = text.split(".")
    if len(parts) == 3 and len(parts[2]) == 4:
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return text


def cell_value(item: dict[str, Any], column: str) -> str:
    raw = item.get(column)
    if column == "documents_count":
        if raw is None:
            return ""
        return str(int(raw))
    if column in BOOL_COLUMNS:
        if raw is None:
            return ""
        return "да" if bool(raw) else "нет"
    if column in DATE_COLUMNS:
        return _as_date_cell(raw)
    if raw is None:
        return ""
    if isinstance(raw, bool):
        return "да" if raw else "нет"
    text = str(raw)
    return escape_formula_cell(text)


def export_filename(fmt: str, *, now: datetime | None = None) -> str:
    stamp = now or datetime.now(MSK)
    local = stamp.astimezone(MSK) if stamp.tzinfo else stamp.replace(tzinfo=MSK)
    return f"inbox-export-{local.strftime('%Y-%m-%d-%H%M')}.{fmt}"


def _document_counts(tender_ids: list[str]) -> dict[str, int]:
    if not tender_ids:
        return {}
    factory = session_factory()
    with factory() as session:
        rows = session.execute(
            select(Document.tender_id, func.count())
            .where(Document.tender_id.in_(tuple(tender_ids)))
            .group_by(Document.tender_id)
        ).all()
    return {str(tid): int(n) for tid, n in rows}


def build_export_rows(
    items: list[dict[str, Any]], columns: list[str]
) -> list[list[str]]:
    need_docs = "documents_count" in columns
    counts: dict[str, int] = {}
    if need_docs:
        counts = _document_counts([str(item.get("tender_id") or "") for item in items])
    headers = [EXPORT_COLUMN_HEADERS[key] for key in columns]
    rows: list[list[str]] = [headers]
    for item in items:
        enriched = dict(item)
        if need_docs:
            tid = str(item.get("tender_id") or "")
            enriched["documents_count"] = counts.get(tid, 0)
        rows.append([cell_value(enriched, col) for col in columns])
    return rows


def render_csv(rows: list[list[str]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")


def render_xlsx(rows: list[list[str]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "inbox"
    for row in rows:
        ws.append(row)
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def export_inbox(body: Any) -> tuple[bytes, str, str]:
    """Return (payload, filename, media_type)."""
    fmt, columns, filters = parse_export_body(body)
    listed = list_inbox(
        unread=filters["unread"],
        tier=filters["tier"],
        q=filters["q"],
        deadline_from=filters["deadline_from"],
        deadline_to=filters["deadline_to"],
        ingested_from=filters["ingested_from"],
        ingested_to=filters["ingested_to"],
        ai_reviewed=filters["ai_reviewed"],
        ai_trigger=filters["ai_trigger"],
        ai_error=filters["ai_error"],
        ai_wrong=filters["ai_wrong"],
        price_min_rub=filters["price_min_rub"],
        platform=filters["platform"],
        bitrix=filters["bitrix"],
        sort=filters["sort"],
    )
    items = listed.get("items") or []
    if not isinstance(items, list):
        items = []
    rows = build_export_rows(items, columns)
    filename = export_filename(fmt)
    if fmt == "csv":
        return render_csv(rows), filename, "text/csv; charset=utf-8"
    return (
        render_xlsx(rows),
        filename,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

"""Unit: inbox export CSV/XLSX helpers and route registration."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.api.inbox import InboxQueryError, parse_ai_wrong
from app.api.inbox_export import (
    AI_REVIEW_PRESET,
    EXPORT_COLUMN_HEADERS,
    cell_value,
    escape_formula_cell,
    export_filename,
    parse_export_body,
    render_csv,
    render_xlsx,
)
from app.api.main import app

MSK = ZoneInfo("Europe/Moscow")


@pytest.mark.unit
def test_export_route_registered() -> None:
    paths = [getattr(route, "path", "") or "" for route in app.routes]
    assert "/api/inbox/export" in paths


@pytest.mark.unit
def test_parse_ai_wrong() -> None:
    assert parse_ai_wrong(None) is None
    assert parse_ai_wrong("") is None
    assert parse_ai_wrong(True) is True
    assert parse_ai_wrong("1") is True
    assert parse_ai_wrong(False) is False
    assert parse_ai_wrong("0") is False
    with pytest.raises(InboxQueryError):
        parse_ai_wrong("maybe")


@pytest.mark.unit
def test_parse_export_body_ok_and_errors() -> None:
    fmt, cols, filters = parse_export_body(
        {
            "format": "csv",
            "columns": ["tender_id", "title", "tender_id"],
            "tier": "L1",
            "ai_wrong": True,
        }
    )
    assert fmt == "csv"
    assert cols == ["tender_id", "title"]
    assert filters["tier"] == "L1"
    assert filters["ai_wrong"] is True

    with pytest.raises(InboxQueryError):
        parse_export_body({"format": "xlsm", "columns": ["tender_id"]})
    with pytest.raises(InboxQueryError):
        parse_export_body({"format": "csv", "columns": []})
    with pytest.raises(InboxQueryError):
        parse_export_body({"format": "csv", "columns": ["nope"]})


@pytest.mark.unit
def test_formula_escape_and_bool_ru() -> None:
    assert escape_formula_cell("=1+1") == "'=1+1"
    assert escape_formula_cell("+cmd") == "'+cmd"
    assert escape_formula_cell("normal") == "normal"
    assert cell_value({"ai_wrong": True}, "ai_wrong") == "да"
    assert cell_value({"ai_wrong": False}, "ai_wrong") == "нет"
    assert cell_value({"title": "=SUM(1)"}, "title") == "'=SUM(1)"
    assert cell_value({"deadline_msk": "2026-09-10"}, "deadline_msk") == "2026-09-10"
    assert cell_value({"deadline_msk": "20.08.2026 15:00"}, "deadline_msk") == "2026-08-20"


@pytest.mark.unit
def test_export_filename_msk() -> None:
    stamp = datetime(2026, 9, 10, 8, 57, tzinfo=MSK)
    assert export_filename("csv", now=stamp) == "inbox-export-2026-09-10-0857.csv"
    assert export_filename("xlsx", now=stamp).endswith(".xlsx")


@pytest.mark.unit
def test_render_csv_bom_and_ru_headers() -> None:
    rows = [
        [EXPORT_COLUMN_HEADERS["tender_id"], EXPORT_COLUMN_HEADERS["ai_wrong"]],
        ["t1", "да"],
    ]
    raw = render_csv(rows)
    assert raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    assert "Id" in text
    assert "ИИ ошибся" in text
    assert "t1" in text


@pytest.mark.unit
def test_render_xlsx_and_ai_preset_subset() -> None:
    assert "ai_wrong_note" in AI_REVIEW_PRESET
    rows = [["Id", "Название"], ["1", "УЗК"]]
    blob = render_xlsx(rows)
    assert blob[:2] == b"PK"
    assert len(blob) > 100

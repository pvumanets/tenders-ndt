"""Unit: P5.3 ingest mapping — no database."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.worker.cli import cmd_artifacts
from app.worker.ingest import (
    inbox_rows,
    ingest_run,
    lot_differs,
    lot_values,
    parse_price_rub,
    redact_db_error,
)

_NOW = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
_RUN = uuid4()


def _row(**overrides: object) -> dict:
    base: dict = {
        "tender_id": "45289101",
        "title": "УЗК сварных соединений",
        "url": "https://rostender.info/tender/45289101",
        "score": 7,
        "tier": "L1",
        "location": "Москва, Russia, RU",
        "customer_name": "ООО Тест",
        "price_rub": "1 250 000,50 ₽",
        "source_etp": "ТЭК-Торг",
        "fit_reason": "услуга НК",
    }
    base.update(overrides)
    return base


@pytest.mark.unit
def test_inbox_rows_keeps_score_ge_4_and_dedupes() -> None:
    rows = [
        _row(tender_id="a", score=3, title="L3", url="https://x/a"),
        _row(tender_id="b", score=4, title="edge", url="https://x/b"),
        _row(tender_id="c", score=8, title="first", url="https://x/c"),
        _row(tender_id="c", score=8, title="last", url="https://x/c"),
        _row(tender_id="", score=9, title="no-id", url="https://x/z"),
    ]
    kept = inbox_rows(rows)
    ids = [r["tender_id"] for r in kept]
    assert ids == ["b", "c"]
    assert kept[1]["title"] == "last"


@pytest.mark.unit
def test_lot_values_sets_rostender_and_cleans_location() -> None:
    values = lot_values(_row(), run_id=_RUN, ingested_at=_NOW)
    assert values["source_platform_id"] == "rostender"
    assert values["location"] == "Москва"
    assert values["price_rub"] == Decimal("1250000.50")
    assert values["run_id"] == _RUN
    assert values["raw"]["source_etp"] == "ТЭК-Торг"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("", None),
        (1850000, Decimal("1850000.00")),
        ("1850000", Decimal("1850000.00")),
        ("1 250 000,50 ₽", Decimal("1250000.50")),
        (Decimal("10.1"), Decimal("10.10")),
        (True, None),
    ],
)
def test_parse_price_rub(raw: object, expected: Decimal | None) -> None:
    assert parse_price_rub(raw) == expected


@pytest.mark.unit
def test_ingest_run_skips_without_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("POSTGRES_PASSWORD", "")
    monkeypatch.delenv("SCOUT_TEST_DATABASE_URL", raising=False)
    assert ingest_run(query="q", limit_n=10, status="done", rows=[_row()]) is None


@pytest.mark.unit
def test_redact_db_error_strips_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    dsn = "postgresql://user:secret@localhost:5432/scout"
    monkeypatch.setenv("DATABASE_URL", dsn)
    text = redact_db_error(RuntimeError(f"connect {dsn} failed"))
    assert "secret" not in text
    assert "DATABASE_URL" in text


@pytest.mark.unit
def test_lot_differs_title_deadline_price_and_docs() -> None:
    values = lot_values(_row(deadline_msk="2030-01-15", price_rub="100"), run_id=_RUN, ingested_at=_NOW)
    lot = type("Lot", (), {})()
    for key, value in values.items():
        setattr(lot, key, value)
    assert lot_differs(lot, values, _row(deadline_msk="2030-01-15", price_rub="100")) is False
    assert lot_differs(
        lot,
        lot_values(_row(title="other", deadline_msk="2030-01-15", price_rub="100"), run_id=_RUN, ingested_at=_NOW),
        _row(title="other", deadline_msk="2030-01-15", price_rub="100"),
    )
    assert lot_differs(
        lot,
        lot_values(_row(deadline_msk="2030-02-01", price_rub="100"), run_id=_RUN, ingested_at=_NOW),
        _row(deadline_msk="2030-02-01", price_rub="100"),
    )
    assert lot_differs(
        lot,
        lot_values(_row(deadline_msk="2030-01-15", price_rub="200"), run_id=_RUN, ingested_at=_NOW),
        _row(deadline_msk="2030-01-15", price_rub="200"),
    )
    with_docs = _row(deadline_msk="2030-01-15", price_rub="100", doc_links=["a.pdf"])
    assert lot_differs(
        lot,
        lot_values(with_docs, run_id=_RUN, ingested_at=_NOW),
        with_docs,
    )


@pytest.mark.unit
def test_expired_tender_ids_and_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    from datetime import date

    from app.worker import ingest as ingest_mod

    class _FakeLot:
        def __init__(self, tender_id: str, deadline_msk: str | None, score: int = 7) -> None:
            self.tender_id = tender_id
            self.deadline_msk = deadline_msk
            self.score = score

    class _FakeSession:
        def scalars(self, _stmt):  # noqa: ANN001
            class _R:
                def all(self_inner):  # noqa: ANN001
                    return [
                        _FakeLot("a", "2020-01-01"),
                        _FakeLot("b", "2099-01-01"),
                        _FakeLot("c", None),
                    ]

            return _R()

    ids = ingest_mod.expired_tender_ids(_FakeSession(), today=date(2026, 8, 27))
    assert ids == {"a"}

    monkeypatch.setattr(ingest_mod, "database_url", lambda: "")
    assert ingest_mod.snapshot_expired_tender_ids() == set()


@pytest.mark.unit
def test_artifacts_cli_writes_files_when_db_missing(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("POSTGRES_PASSWORD", "")
    monkeypatch.setenv("DOWNLOAD_DOCS", "0")
    monkeypatch.delenv("SCOUT_TEST_DATABASE_URL", raising=False)
    (tmp_path / "scored-list.json").write_text(
        json.dumps([_row(score=7), _row(tender_id="low", score=3, url="https://x/low")]),
        encoding="utf-8",
    )
    rc = cmd_artifacts(argparse.Namespace(out=str(tmp_path)))
    assert rc == 0
    assert (tmp_path / "tenders.md").is_file()
    assert (tmp_path / "tenders.csv").is_file()
    assert (tmp_path / "priority-fit.md").is_file()

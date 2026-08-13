"""Unit: P5.4 inbox parsers, serialization, 401, routes. No database."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.inbox import (
    InboxQueryError,
    deadline_iso,
    list_inbox,
    parse_priority_body,
    parse_query_date,
    parse_unread,
    parse_viewed_body,
    serialize_lot,
)
from app.api.main import app
from app.db.models import Lot, LotState

_SECRET_NEEDLES = ("password", "postgresql+", "database_url", "cookie")


def _client() -> TestClient:
    try:
        return TestClient(app, lifespan="off")
    except TypeError:
        return TestClient(app)


def _assert_no_secrets(body: object) -> None:
    blob = json.dumps(body).lower()
    for needle in _SECRET_NEEDLES:
        assert needle not in blob


def _lot(**overrides: object) -> Lot:
    values: dict = {
        "tender_id": "45289101",
        "title": "УЗК сварных соединений",
        "url": "https://rostender.info/tender/45289101",
        "score": 7,
        "tier": "L1",
        "location": "Казань",
        "customer_name": "ООО Тест",
        "deadline_msk": "20.08.2026 15:00",
        "status": "Приём заявок",
        "fit_reason": "услуга НК",
        "source_platform_id": "rostender",
        "price_rub": Decimal("1850000.00"),
        "ingested_at": datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return Lot(**values)


@pytest.mark.unit
def test_inbox_routes_include_documents() -> None:
    with _client() as client:
        paths = [getattr(route, "path", "") or "" for route in client.app.routes]
    assert "/api/inbox" in paths
    assert "/api/inbox/{tender_id}" in paths
    assert "/api/inbox/{tender_id}/viewed" in paths
    assert "/api/inbox/{tender_id}/priority" in paths
    assert "/api/inbox/{tender_id}/documents" in paths
    assert "/api/inbox/{tender_id}/documents/{filename}" in paths


@pytest.mark.unit
def test_inbox_unauthorized_without_cookie() -> None:
    with _client() as client:
        listing = client.get("/api/inbox")
        one = client.get("/api/inbox/qa_unit_missing")
        viewed = client.put("/api/inbox/qa_unit_missing/viewed", json={"viewed": True})
        priority = client.put("/api/inbox/qa_unit_missing/priority", json={"tier": "L1"})
        docs = client.get("/api/inbox/qa_unit_missing/documents")
        download = client.get("/api/inbox/qa_unit_missing/documents/TZ.pdf")
    assert listing.status_code == 401
    assert one.status_code == 401
    assert viewed.status_code == 401
    assert priority.status_code == 401
    assert docs.status_code == 401
    assert download.status_code == 401
    assert listing.json() == {"detail": "unauthorized"}
    _assert_no_secrets(listing.json())
    _assert_no_secrets(one.json())


@pytest.mark.unit
def test_deadline_iso_parses_dmy_and_iso() -> None:
    assert deadline_iso("20.08.2026") == "2026-08-20"
    assert deadline_iso("20.08.2026 15:00") == "2026-08-20"
    assert deadline_iso("2026-08-20") == "2026-08-20"
    assert deadline_iso("nope") == "nope"
    assert deadline_iso(None) is None


@pytest.mark.unit
def test_list_inbox_rejects_bad_query_before_db() -> None:
    with pytest.raises(InboxQueryError, match="invalid_tier"):
        list_inbox(tier="L9")
    with pytest.raises(InboxQueryError, match="invalid_date"):
        list_inbox(deadline_from="13.08.2026")
    with pytest.raises(InboxQueryError, match="invalid_unread"):
        parse_unread("maybe")
    with pytest.raises(InboxQueryError, match="invalid_date"):
        parse_query_date("2026-13-01")


@pytest.mark.unit
def test_serialize_lot_iso_dates_and_effective_tier() -> None:
    lot = _lot()
    item = serialize_lot(lot, None)
    assert item["deadline_msk"] == "2026-08-20"
    assert item["ingested_at"] == "2026-08-12"
    assert item["viewed"] is False
    assert item["manual_tier"] is None
    assert item["effective_tier"] == "L1"
    assert item["price_rub"] == 1850000
    assert item["source_platform_id"] == "rostender"
    assert "documents" not in item
    _assert_no_secrets(item)

    state = LotState(tender_id=lot.tender_id, viewed=True, manual_tier="L2")
    card = serialize_lot(lot, state, include_documents=True, documents=[])
    assert card["effective_tier"] == "L2"
    assert card["manual_tier"] == "L2"
    assert card["viewed"] is True
    assert card["documents"] == []
    _assert_no_secrets(card)


@pytest.mark.unit
def test_parse_bodies() -> None:
    assert parse_viewed_body({"viewed": True}) is True
    assert parse_viewed_body({"viewed": False}) is False
    with pytest.raises(InboxQueryError, match="invalid_body"):
        parse_viewed_body({"viewed": 1})
    with pytest.raises(InboxQueryError, match="invalid_body"):
        parse_viewed_body({})
    assert parse_priority_body({"tier": None}) is None
    assert parse_priority_body({"tier": "L3"}) == "L3"
    with pytest.raises(InboxQueryError, match="invalid_tier"):
        parse_priority_body({"tier": "L9"})
    with pytest.raises(InboxQueryError, match="invalid_body"):
        parse_priority_body({"tier": "L1", "extra": True})

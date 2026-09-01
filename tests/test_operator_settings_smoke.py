"""Smoke: operator-settings GET/PUT + inbox price/platform/bitrix filters."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.operator_settings import DEFAULT_L1_MIN_PRICE_RUB
from app.api.main import app
from app.db.models import Document, Lot, LotState, OperatorSettings, Run, ScoutSession, User
from tests.conftest import SMOKE_PREFIX

_PASS = "qa-smoke-operator-settings-pass"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _client() -> TestClient:
    try:
        return TestClient(app, lifespan="off")
    except TypeError:
        return TestClient(app)


def _cleanup(
    factory: sessionmaker[Session],
    *,
    username: str,
    lot_ids: list[str],
    query: str,
) -> None:
    with factory() as session:
        user = session.scalar(select(User).where(User.username == username))
        if user is not None:
            session.execute(delete(ScoutSession).where(ScoutSession.user_id == user.id))
            session.delete(user)
        if lot_ids:
            session.execute(delete(Document).where(Document.tender_id.in_(lot_ids)))
            session.execute(delete(LotState).where(LotState.tender_id.in_(lot_ids)))
            session.execute(delete(Lot).where(Lot.tender_id.in_(lot_ids)))
        session.execute(delete(Run).where(Run.query == query))
        session.commit()


@pytest.mark.smoke
def test_operator_settings_and_inbox_price_filters(smoke_db: sessionmaker[Session]) -> None:
    suffix = uuid4().hex[:12]
    username = f"{SMOKE_PREFIX}opset_{suffix}"
    cheap_id = f"{SMOKE_PREFIX}cheap_{suffix}"
    rich_id = f"{SMOKE_PREFIX}rich_{suffix}"
    null_id = f"{SMOKE_PREFIX}null_{suffix}"
    rost_id = f"{SMOKE_PREFIX}rost_{suffix}"
    query = f"{SMOKE_PREFIX}opset_run_{suffix}"
    lot_ids = [cheap_id, rich_id, null_id, rost_id]
    saved_price = DEFAULT_L1_MIN_PRICE_RUB
    try:
        with smoke_db() as session:
            session.add(
                User(
                    username=username,
                    password_hash=_hash(_PASS),
                    display_name="qa_smoke_operator_settings",
                )
            )
            session.add(Run(query=query, status="done", limit_n=10, pipeline="auto"))
            session.flush()
            run = session.scalar(select(Run).where(Run.query == query))
            assert run is not None
            rows = [
                (
                    cheap_id,
                    Decimal("50000"),
                    "rostender",
                    LotState(
                        tender_id=cheap_id,
                        ai_reviewed_at=datetime(2026, 8, 30, 7, 0, tzinfo=timezone.utc),
                        ai_tier="L1",
                        ai_trigger="auto",
                    ),
                ),
                (
                    rich_id,
                    Decimal("500000"),
                    "rostender",
                    LotState(
                        tender_id=rich_id,
                        ai_reviewed_at=datetime(2026, 8, 30, 7, 0, tzinfo=timezone.utc),
                        ai_tier="L1",
                        ai_trigger="auto",
                    ),
                ),
                (
                    null_id,
                    None,
                    "rostender",
                    LotState(
                        tender_id=null_id,
                        ai_reviewed_at=datetime(2026, 8, 30, 7, 0, tzinfo=timezone.utc),
                        ai_tier="L1",
                        ai_trigger="auto",
                    ),
                ),
                (
                    rost_id,
                    Decimal("200000"),
                    "roseltorg",
                    LotState(
                        tender_id=rost_id,
                        ai_reviewed_at=datetime(2026, 8, 30, 7, 0, tzinfo=timezone.utc),
                        ai_tier="L2",
                        ai_trigger="auto",
                    ),
                ),
            ]
            for tid, price, platform, state in rows:
                session.add(
                    Lot(
                        tender_id=tid,
                        run_id=run.id,
                        title=f"Smoke {tid}",
                        url=f"https://rostender.info/tender/{tid}",
                        score=7,
                        tier="L1",
                        location="Москва",
                        customer_name="ООО Smoke",
                        deadline_msk="20.09.2026",
                        status="Приём заявок",
                        fit_reason="услуга НК",
                        source_platform_id=platform,
                        price_rub=price,
                        ingested_at=datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc),
                    )
                )
                session.add(state)
            session.commit()

        with _client() as client:
            assert client.get("/api/operator-settings").status_code == 401
            login = client.post(
                "/api/auth/login",
                json={"username": username, "password": _PASS},
            )
            assert login.status_code == 200

            got = client.get("/api/operator-settings")
            assert got.status_code == 200
            body = got.json()
            assert body["l1_min_price_rub"] == DEFAULT_L1_MIN_PRICE_RUB
            saved_price = int(body["l1_min_price_rub"])

            bad = client.put("/api/operator-settings", json={"l1_min_price_rub": -1})
            assert bad.status_code == 400
            assert bad.json() == {"detail": "invalid_l1_min_price_rub"}

            put = client.put("/api/operator-settings", json={"l1_min_price_rub": 250_000})
            assert put.status_code == 200
            assert put.json()["l1_min_price_rub"] == 250_000

            filtered = client.get(
                "/api/inbox",
                params={"ai_reviewed": "1", "ai_trigger": "auto", "price_min_rub": "100000"},
            )
            assert filtered.status_code == 200
            ids = {row["tender_id"] for row in filtered.json()["items"]}
            assert cheap_id not in ids
            assert rich_id in ids
            assert null_id in ids

            rich_item = next(
                row for row in filtered.json()["items"] if row["tender_id"] == rich_id
            )
            assert rich_item["ai_tier"] == "L1"
            assert rich_item["effective_tier"] == "L1"

            capped = client.get(
                "/api/inbox",
                params={"ai_reviewed": "1", "ai_trigger": "auto", "price_min_rub": "0"},
            )
            assert capped.status_code == 200
            capped_cheap = next(
                row for row in capped.json()["items"] if row["tender_id"] == cheap_id
            )
            assert capped_cheap["effective_tier"] == "L2"

            platform = client.get(
                "/api/inbox",
                params={"ai_reviewed": "1", "ai_trigger": "auto", "platform": "roseltorg"},
            )
            assert platform.status_code == 200
            platform_ids = {row["tender_id"] for row in platform.json()["items"]}
            assert rost_id in platform_ids
            assert rich_id not in platform_ids

            bitrix_in = client.get(
                "/api/inbox",
                params={"ai_reviewed": "1", "ai_trigger": "auto", "bitrix": "in"},
            )
            assert bitrix_in.status_code == 200
            assert bitrix_in.json()["items"] == []

            bitrix_out = client.get(
                "/api/inbox",
                params={"ai_reviewed": "1", "ai_trigger": "auto", "bitrix": "out"},
            )
            assert bitrix_out.status_code == 200
            out_ids = {row["tender_id"] for row in bitrix_out.json()["items"]}
            assert rich_id in out_ids
            assert rost_id in out_ids
    finally:
        with smoke_db() as session:
            row = session.get(OperatorSettings, 1)
            if row is not None:
                row.l1_min_price_rub = saved_price
                session.commit()
        _cleanup(smoke_db, username=username, lot_ids=lot_ids, query=query)

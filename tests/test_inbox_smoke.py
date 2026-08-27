"""Smoke: P5.4 inbox reads/writes Postgres; score ≥ 4 pool; lot_state persists."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.main import app
from app.db.models import Document, Lot, LotState, Run, ScoutSession, User
from tests.conftest import SMOKE_PREFIX

_PASS = "qa-smoke-inbox-pass"


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
def test_inbox_pool_viewed_priority_persist(smoke_db: sessionmaker[Session]) -> None:
    suffix = uuid4().hex[:12]
    username = f"{SMOKE_PREFIX}inbox_{suffix}"
    hot_id = f"{SMOKE_PREFIX}hot_{suffix}"
    low_id = f"{SMOKE_PREFIX}low_{suffix}"
    query = f"{SMOKE_PREFIX}inbox_run_{suffix}"
    lot_ids = [hot_id, low_id]
    try:
        with smoke_db() as session:
            session.add(
                User(
                    username=username,
                    password_hash=_hash(_PASS),
                    display_name="qa_smoke_inbox",
                )
            )
            session.add(
                Run(query=query, status="done", limit_n=10)
            )
            session.flush()
            run = session.scalar(select(Run).where(Run.query == query))
            assert run is not None
            session.add(
                Lot(
                    tender_id=hot_id,
                    run_id=run.id,
                    title="УЗК сварных соединений (smoke)",
                    url=f"https://rostender.info/tender/{hot_id}",
                    score=7,
                    tier="L1",
                    location="Казань",
                    customer_name="ООО Smoke",
                    deadline_msk="20.08.2026",
                    status="Приём заявок",
                    fit_reason="услуга НК",
                    source_platform_id="rostender",
                    ingested_at=datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc),
                )
            )
            session.add(
                Lot(
                    tender_id=low_id,
                    run_id=run.id,
                    title="авто-L3 не в inbox",
                    url=f"https://rostender.info/tender/{low_id}",
                    score=3,
                    tier="L3",
                    location="Москва",
                    customer_name="ООО Low",
                    source_platform_id="rostender",
                    ingested_at=datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc),
                )
            )
            session.commit()

        with _client() as client:
            login = client.post(
                "/api/auth/login",
                json={"username": username, "password": _PASS},
            )
            assert login.status_code == 200
            bad_tier = client.get("/api/inbox", params={"tier": "L9"})
            assert bad_tier.status_code == 400
            assert bad_tier.json() == {"detail": "invalid_tier"}
            listing = client.get("/api/inbox")
            assert listing.status_code == 200
            body = listing.json()
            ids = [row["tender_id"] for row in body["items"]]
            assert hot_id in ids
            assert low_id not in ids
            assert body["total"] == len(body["items"])
            hot = next(row for row in body["items"] if row["tender_id"] == hot_id)
            assert hot["score"] == 7
            assert hot["deadline_msk"] == "2026-08-20"
            assert hot["ingested_at"] == "2026-08-12"
            assert hot["effective_tier"] == "L1"
            assert hot["viewed"] is False
            assert hot["deadline_expired"] is True
            assert hot["board_hidden"] is False
            assert "documents" not in hot
            blob = json.dumps(body).lower()
            assert "password" not in blob
            assert "postgresql+" not in blob

            missing = client.get("/api/inbox/qa_smoke_missing_id")
            assert missing.status_code == 404
            out_of_pool = client.get(f"/api/inbox/{low_id}")
            assert out_of_pool.status_code == 404

            viewed = client.put(f"/api/inbox/{hot_id}/viewed", json={"viewed": True})
            assert viewed.status_code == 200
            assert viewed.json()["viewed"] is True
            assert viewed.json()["documents"] == []
            prio = client.put(f"/api/inbox/{hot_id}/priority", json={"tier": "L2"})
            assert prio.status_code == 200
            assert prio.json()["manual_tier"] == "L2"
            assert prio.json()["effective_tier"] == "L2"
            assert client.put(f"/api/inbox/{low_id}/viewed", json={"viewed": True}).status_code == 404

            archived = client.put(f"/api/inbox/{hot_id}/board-hidden", json={"hidden": True})
            assert archived.status_code == 200
            assert archived.json()["board_hidden"] is True
            listing_hidden = client.get("/api/inbox")
            assert hot_id not in [row["tender_id"] for row in listing_hidden.json()["items"]]
            still = client.get(f"/api/inbox/{hot_id}")
            assert still.status_code == 200
            assert still.json()["board_hidden"] is True
            restored = client.put(f"/api/inbox/{hot_id}/board-hidden", json={"hidden": False})
            assert restored.status_code == 200
            assert restored.json()["board_hidden"] is False
            assert hot_id in [row["tender_id"] for row in client.get("/api/inbox").json()["items"]]

        with _client() as client:
            login = client.post(
                "/api/auth/login",
                json={"username": username, "password": _PASS},
            )
            assert login.status_code == 200
            card = client.get(f"/api/inbox/{hot_id}")
            assert card.status_code == 200
            payload = card.json()
            assert payload["viewed"] is True
            assert payload["manual_tier"] == "L2"
            assert payload["effective_tier"] == "L2"
            unread = client.get("/api/inbox", params={"unread": "true"})
            assert unread.status_code == 200
            assert hot_id not in [row["tender_id"] for row in unread.json()["items"]]
            by_tier = client.get("/api/inbox", params={"tier": "L2"})
            assert hot_id in [row["tender_id"] for row in by_tier.json()["items"]]
            reset = client.put(f"/api/inbox/{hot_id}/priority", json={"tier": None})
            assert reset.status_code == 200
            assert reset.json()["manual_tier"] is None
            assert reset.json()["effective_tier"] == "L1"
            ranged = client.get(
                "/api/inbox",
                params={"deadline_from": "2026-08-19", "deadline_to": "2026-08-21"},
            )
            assert hot_id in [row["tender_id"] for row in ranged.json()["items"]]
    finally:
        _cleanup(smoke_db, username=username, lot_ids=lot_ids, query=query)

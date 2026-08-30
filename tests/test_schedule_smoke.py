"""Smoke: schedule GET/PUT auth + inbox ai_trigger. Cleans qa_smoke_* rows."""
from __future__ import annotations

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

_PASS = "qa-smoke-schedule-pass"


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
def test_schedule_get_put_and_inbox_ai_trigger(smoke_db: sessionmaker[Session]) -> None:
    suffix = uuid4().hex[:12]
    username = f"{SMOKE_PREFIX}sched_{suffix}"
    auto_id = f"{SMOKE_PREFIX}auto_{suffix}"
    manual_id = f"{SMOKE_PREFIX}man_{suffix}"
    query = f"{SMOKE_PREFIX}sched_run_{suffix}"
    lot_ids = [auto_id, manual_id]
    saved_enabled = True
    saved_time = "07:00"
    try:
        with smoke_db() as session:
            session.add(
                User(
                    username=username,
                    password_hash=_hash(_PASS),
                    display_name="qa_smoke_schedule",
                )
            )
            session.add(Run(query=query, status="done", limit_n=10, pipeline="auto"))
            session.flush()
            run = session.scalar(select(Run).where(Run.query == query))
            assert run is not None
            for tid, trigger in ((auto_id, "auto"), (manual_id, "manual")):
                session.add(
                    Lot(
                        tender_id=tid,
                        run_id=run.id,
                        title=f"УЗК smoke {trigger}",
                        url=f"https://rostender.info/tender/{tid}",
                        score=7,
                        tier="L1",
                        location="Москва",
                        customer_name="ООО Smoke",
                        deadline_msk="20.09.2026",
                        status="Приём заявок",
                        fit_reason="услуга НК",
                        source_platform_id="rostender",
                        ingested_at=datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc),
                    )
                )
                session.add(
                    LotState(
                        tender_id=tid,
                        ai_reviewed_at=datetime(2026, 8, 30, 7, 0, tzinfo=timezone.utc),
                        ai_tier="L1",
                        ai_trigger=trigger,
                    )
                )
            session.commit()

        with _client() as client:
            assert client.get("/api/schedule").status_code == 401
            login = client.post(
                "/api/auth/login",
                json={"username": username, "password": _PASS},
            )
            assert login.status_code == 200
            got = client.get("/api/schedule")
            assert got.status_code == 200
            body = got.json()
            assert "enabled" in body
            assert body["time_msk"]
            saved_enabled = bool(body["enabled"])
            saved_time = str(body["time_msk"])
            bad = client.put("/api/schedule", json={"time_msk": "25:00"})
            assert bad.status_code == 400
            assert bad.json() == {"detail": "invalid_time_msk"}
            put = client.put("/api/schedule", json={"enabled": saved_enabled, "time_msk": saved_time})
            assert put.status_code == 200
            assert put.json()["time_msk"] == saved_time

            status = client.get("/api/status")
            assert status.status_code == 200
            snap = status.json()
            assert snap["pipeline"] in {"manual", "auto"}
            assert snap["ai_review_done"] == 0 or isinstance(snap["ai_review_done"], int)
            assert "ai_review_total" in snap

            bad_trigger = client.get("/api/inbox", params={"ai_trigger": "both"})
            assert bad_trigger.status_code == 400
            assert bad_trigger.json() == {"detail": "invalid_ai_trigger"}
            auto_list = client.get(
                "/api/inbox", params={"ai_reviewed": "1", "ai_trigger": "auto"}
            )
            assert auto_list.status_code == 200
            auto_ids = [row["tender_id"] for row in auto_list.json()["items"]]
            assert auto_id in auto_ids
            assert manual_id not in auto_ids
            man_list = client.get(
                "/api/inbox", params={"ai_reviewed": "1", "ai_trigger": "manual"}
            )
            man_ids = [row["tender_id"] for row in man_list.json()["items"]]
            assert manual_id in man_ids
            assert auto_id not in man_ids
            start = client.post("/api/run/start", json={"pipeline": "nope"})
            assert start.status_code == 400
            assert start.json() == {"detail": "invalid_pipeline"}
    finally:
        with smoke_db() as session:
            from app.db.models import ScheduleSettings

            row = session.get(ScheduleSettings, 1)
            if row is not None:
                row.enabled = saved_enabled
                row.time_msk = saved_time
                session.commit()
        _cleanup(smoke_db, username=username, lot_ids=lot_ids, query=query)

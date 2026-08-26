"""Smoke: P5.5 document list + download behind session; files on volume."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.main import app
from app.db.models import Document, Lot, LotState, Run, ScoutSession, User
from tests.conftest import SMOKE_PREFIX

_PASS = "qa-smoke-docs-pass"


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
def test_documents_list_and_download_require_session(
    smoke_db: sessionmaker[Session],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suffix = uuid4().hex[:12]
    username = f"{SMOKE_PREFIX}docs_{suffix}"
    hot_id = f"rostender:{SMOKE_PREFIX}hot_{suffix}"
    low_id = f"rostender:{SMOKE_PREFIX}low_{suffix}"
    query = f"{SMOKE_PREFIX}docs_run_{suffix}"
    filename = "qa_smoke_tz.pdf"
    payload = b"%PDF-qa-smoke"
    monkeypatch.setenv("SCOUT_DOCS_DIR", str(tmp_path))
    from app.worker.platform_ids import volume_dir_name

    dest = tmp_path / volume_dir_name(hot_id)
    dest.mkdir(parents=True)
    (dest / filename).write_bytes(payload)
    lot_ids = [hot_id, low_id]
    try:
        with smoke_db() as session:
            session.add(
                User(
                    username=username,
                    password_hash=_hash(_PASS),
                    display_name="qa_smoke_docs",
                )
            )
            session.add(Run(query=query, status="done", limit_n=10))
            session.flush()
            run = session.scalar(select(Run).where(Run.query == query))
            assert run is not None
            session.add(
                Lot(
                    tender_id=hot_id,
                    run_id=run.id,
                    title="УЗК smoke docs",
                    url=f"https://rostender.info/tender/{hot_id}",
                    score=7,
                    tier="L1",
                    location="Казань",
                    source_platform_id="rostender",
                    ingested_at=datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc),
                )
            )
            session.add(
                Lot(
                    tender_id=low_id,
                    run_id=run.id,
                    title="авто-L3",
                    url=f"https://rostender.info/tender/{low_id}",
                    score=3,
                    tier="L3",
                    source_platform_id="rostender",
                    ingested_at=datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc),
                )
            )
            session.add(
                Document(
                    tender_id=hot_id,
                    filename=filename,
                    size_bytes=len(payload),
                    volume_path=f"{volume_dir_name(hot_id)}/{filename}",
                )
            )
            session.commit()

        with _client() as client:
            listing = client.get(f"/api/inbox/{hot_id}/documents")
            assert listing.status_code == 401
            login = client.post(
                "/api/auth/login",
                json={"username": username, "password": _PASS},
            )
            assert login.status_code == 200
            out_of_pool = client.get(f"/api/inbox/{low_id}/documents")
            assert out_of_pool.status_code == 404
            docs = client.get(f"/api/inbox/{hot_id}/documents")
            assert docs.status_code == 200
            body = docs.json()
            assert body["items"][0]["name"] == filename
            assert "url" in body["items"][0]
            blob = json.dumps(body).lower()
            assert "password" not in blob
            assert "postgresql+" not in blob
            card = client.get(f"/api/inbox/{hot_id}")
            assert card.status_code == 200
            assert card.json()["documents"] == [{"name": filename, "size_kb": 0}]
            downloaded = client.get(f"/api/inbox/{hot_id}/documents/{filename}")
            assert downloaded.status_code == 200
            assert downloaded.content == payload
            missing = client.get(f"/api/inbox/{hot_id}/documents/missing.pdf")
            assert missing.status_code == 404
            sneaky = client.get(f"/api/inbox/{hot_id}/documents/%2e%2e%2f{filename}")
            assert sneaky.status_code in {400, 404, 422}
            assert sneaky.content != payload
            # Starlette collapses `/documents/..` to the lot card; must not be file bytes.
            traversal = client.get(f"/api/inbox/{hot_id}/documents/..")
            assert traversal.content != payload
    finally:
        _cleanup(smoke_db, username=username, lot_ids=lot_ids, query=query)

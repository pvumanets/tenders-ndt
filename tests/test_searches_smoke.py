"""Smoke: searches CRUD, unique name, empty_queue, 409. Cleans qa_smoke_*."""
from __future__ import annotations

from uuid import uuid4

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.main import app
from app.api.state import STATE
from app.db.models import NamedSearch, Run, ScoutSession, User
from tests.conftest import SMOKE_PREFIX

_PASS = "qa-smoke-searches-pass"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _client() -> TestClient:
    try:
        return TestClient(app, lifespan="off")
    except TypeError:
        return TestClient(app)


def _body(item: dict, **overrides: object) -> dict:
    payload = {
        "name": item["name"],
        "platform_id": item["platform_id"],
        "queries": item["queries"],
        "limit_n": item["limit_n"],
        "in_queue": item["in_queue"],
        "sort_order": item["sort_order"],
    }
    payload.update(overrides)
    return payload


def _cleanup(factory: sessionmaker[Session], *, username: str, search_name: str) -> None:
    with factory() as session:
        user = session.scalar(select(User).where(User.username == username))
        if user is not None:
            session.execute(delete(ScoutSession).where(ScoutSession.user_id == user.id))
            session.delete(user)
        row = session.scalar(select(NamedSearch).where(NamedSearch.name == search_name))
        if row is not None:
            session.execute(delete(Run).where(Run.search_id == row.id))
            session.delete(row)
        session.commit()


@pytest.mark.smoke
def test_searches_crud_unique_empty_queue_conflict(smoke_db: sessionmaker[Session]) -> None:
    suffix = uuid4().hex[:12]
    username = f"{SMOKE_PREFIX}search_{suffix}"
    search_name = f"{SMOKE_PREFIX}named_{suffix}"
    original: list[dict] = []
    STATE.running = False
    try:
        with smoke_db() as session:
            session.add(
                User(
                    username=username,
                    password_hash=_hash(_PASS),
                    display_name="qa_smoke_searches",
                )
            )
            session.commit()
        with _client() as client:
            login = client.post("/api/auth/login", json={"username": username, "password": _PASS})
            assert login.status_code == 200
            listing = client.get("/api/searches")
            assert listing.status_code == 200
            names = {item["name"] for item in listing.json()["items"]}
            assert "РосТендер НК" in names
            assert "Tender.Pro НК" in names
            created = client.post(
                "/api/searches",
                json={
                    "name": search_name,
                    "platform_id": "rostender",
                    "queries": ["узк"],
                    "limit_n": 10,
                    "in_queue": False,
                    "sort_order": 90,
                },
            )
            assert created.status_code == 200
            search_id = created.json()["id"]
            assert created.json()["queries"] == ["узк"]
            dup = client.post(
                "/api/searches",
                json={
                    "name": search_name,
                    "platform_id": "tender-pro",
                    "queries": ["ВИК"],
                    "limit_n": 5,
                    "in_queue": False,
                    "sort_order": 91,
                },
            )
            assert dup.status_code == 409
            assert dup.json()["detail"] == "duplicate_name"
            updated = client.put(
                f"/api/searches/{search_id}",
                json={
                    "name": search_name,
                    "platform_id": "rostender",
                    "queries": ["пвк", "узк"],
                    "limit_n": 20,
                    "in_queue": False,
                    "sort_order": 90,
                },
            )
            assert updated.status_code == 200
            assert updated.json()["queries"] == ["пвк", "узк"]
            original = client.get("/api/searches").json()["items"]
            try:
                for item in original:
                    if item["in_queue"]:
                        off = client.put(f"/api/searches/{item['id']}", json=_body(item, in_queue=False))
                        assert off.status_code == 200
                empty = client.post("/api/run/start", json={})
                assert empty.status_code == 400
                assert empty.json()["detail"] == "empty_queue"
                STATE.running = True
                conflict = client.post("/api/run/start", json={})
                assert conflict.status_code == 409
                assert conflict.json()["detail"] == "already_running"
            finally:
                STATE.running = False
                for item in original:
                    client.put(f"/api/searches/{item['id']}", json=_body(item))
            deleted = client.delete(f"/api/searches/{search_id}")
            assert deleted.status_code == 204
            leftover = {item["name"] for item in client.get("/api/searches").json()["items"]}
            assert search_name not in leftover
    finally:
        STATE.running = False
        _cleanup(smoke_db, username=username, search_name=search_name)

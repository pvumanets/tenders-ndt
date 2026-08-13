"""Smoke: login cookie, /api/me, logout, password rotation invalidates sessions."""
from __future__ import annotations

from uuid import uuid4

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.api.main import app
from app.db.bootstrap import bootstrap_users
from app.db.models import ScoutSession, User
from tests.conftest import SMOKE_PREFIX

_OLD = "qa-smoke-old-pass"
_NEW = "qa-smoke-new-pass"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _client() -> TestClient:
    try:
        return TestClient(app, lifespan="off")
    except TypeError:
        return TestClient(app)


def _delete_user(factory: sessionmaker[Session], username: str) -> None:
    from sqlalchemy import delete

    with factory() as session:
        user = session.scalar(select(User).where(User.username == username))
        if user is None:
            return
        session.execute(delete(ScoutSession).where(ScoutSession.user_id == user.id))
        session.delete(user)
        session.commit()


@pytest.mark.smoke
def test_login_me_logout_roundtrip(smoke_db: sessionmaker[Session]) -> None:
    username = f"{SMOKE_PREFIX}login_{uuid4().hex[:8]}"
    password = "qa-smoke-login-pass"
    try:
        with smoke_db() as session:
            session.add(
                User(
                    username=username,
                    password_hash=_hash(password),
                    display_name="qa_smoke_login",
                )
            )
            session.commit()
        with _client() as client:
            bad = client.post(
                "/api/auth/login",
                json={"username": username, "password": "wrong-pass"},
            )
            assert bad.status_code == 401
            assert bad.json() == {"detail": "invalid_credentials"}
            ok = client.post(
                "/api/auth/login",
                json={"username": username, "password": password},
            )
            assert ok.status_code == 200
            me = client.get("/api/me")
            assert me.status_code == 200
            body = me.json()
            assert body == {"username": username, "display_name": "qa_smoke_login"}
            assert "password" not in body
            status = client.get("/api/status")
            assert status.status_code == 200
            logged_out = client.post("/api/auth/logout")
            assert logged_out.status_code == 204
            assert client.get("/api/me").status_code == 401
            assert client.get("/api/status").status_code == 401
    finally:
        _delete_user(smoke_db, username)


@pytest.mark.smoke
def test_password_rotation_invalidates_sessions(
    smoke_db: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suffix = uuid4().hex[:8]
    username = f"{SMOKE_PREFIX}rot_{suffix}"
    other = f"{SMOKE_PREFIX}rot_other_{suffix}"
    try:
        with smoke_db() as session:
            session.add(
                User(
                    username=username,
                    password_hash=_hash(_OLD),
                    display_name="qa_smoke_rot",
                )
            )
            session.commit()
        with _client() as client:
            logged_in = client.post(
                "/api/auth/login",
                json={"username": username, "password": _OLD},
            )
            assert logged_in.status_code == 200
            assert client.get("/api/me").status_code == 200
            monkeypatch.setenv("SCOUT_DIGITAL_USERNAME", username)
            monkeypatch.setenv("SCOUT_DIGITAL_PASSWORD", _NEW)
            monkeypatch.setenv("SCOUT_DIRECTOR_USERNAME", other)
            monkeypatch.setenv("SCOUT_DIRECTOR_PASSWORD", "qa-smoke-unused")
            bootstrap_users()
            assert client.get("/api/me").status_code == 401
            still_old = client.post(
                "/api/auth/login",
                json={"username": username, "password": _OLD},
            )
            assert still_old.status_code == 401
            assert still_old.json() == {"detail": "invalid_credentials"}
            renewed = client.post(
                "/api/auth/login",
                json={"username": username, "password": _NEW},
            )
            assert renewed.status_code == 200
            me = client.get("/api/me")
            assert me.status_code == 200
            assert me.json()["username"] == username
    finally:
        _delete_user(smoke_db, username)
        _delete_user(smoke_db, other)

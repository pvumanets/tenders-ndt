"""Smoke: POST cookies → jar → session without values. Cleans qa_smoke_*."""
from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.api import platforms as platforms_api
from app.api.main import app
from app.db.models import ScoutSession, User
from app.worker.cookies import parse_netscape_cookies
from tests.conftest import SMOKE_PREFIX

_PASS = "qa-smoke-cookies-pass"
_SECRET = "qa055_smoke_secret_value_do_not_echo"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _client() -> TestClient:
    try:
        return TestClient(app, lifespan="off")
    except TypeError:
        return TestClient(app)


def _cleanup(factory: sessionmaker[Session], *, username: str) -> None:
    with factory() as session:
        user = session.scalar(select(User).where(User.username == username))
        if user is not None:
            session.execute(delete(ScoutSession).where(ScoutSession.user_id == user.id))
            session.delete(user)
        session.commit()


def _assert_no_secret(body: object) -> None:
    blob = json.dumps(body, ensure_ascii=False)
    assert _SECRET not in blob
    assert "Netscape HTTP Cookie File" not in blob


@pytest.mark.smoke
def test_cookies_upload_smoke(
    smoke_db: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    suffix = uuid4().hex[:12]
    username = f"{SMOKE_PREFIX}cookies_{suffix}"
    jar = tmp_path / "cookies.rostender.txt"
    monkeypatch.setenv("ROSTENDER_COOKIES_FILE", str(jar))
    monkeypatch.setattr(platforms_api, "_probe_platform", lambda platform_id: "ok")
    monkeypatch.setattr(
        platforms_api.notify, "notify_ops_session", lambda **_kw: "smtp_unconfigured"
    )
    payload = [
        {
            "domain": ".rostender.info",
            "name": "PHPSESSID",
            "value": _SECRET,
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "expirationDate": 1893456000.5,
        }
    ]
    try:
        with smoke_db() as session:
            session.add(
                User(
                    username=username,
                    password_hash=_hash(_PASS),
                    display_name="qa_smoke_cookies",
                )
            )
            session.commit()

        with _client() as client:
            assert client.post(
                "/api/platforms/rostender/cookies", json=payload
            ).status_code == 401
            login = client.post(
                "/api/auth/login",
                json={"username": username, "password": _PASS},
            )
            assert login.status_code == 200

            bad = client.post("/api/platforms/rostender/cookies", json=[])
            assert bad.status_code == 400
            assert bad.json()["detail"] in {"empty_cookies", "invalid_cookies_json"}
            _assert_no_secret(bad.json())

            unknown = client.post("/api/platforms/oilb2bcs/cookies", json=payload)
            assert unknown.status_code == 404
            assert unknown.json() == {"detail": "not_found"}
            _assert_no_secret(unknown.json())

            ok = client.post("/api/platforms/rostender/cookies", json=payload)
            assert ok.status_code == 200
            body = ok.json()
            assert body["platform_id"] == "rostender"
            assert body["session"] == "ok"
            assert body["probed"] is True
            _assert_no_secret(body)

            assert jar.is_file()
            parsed = parse_netscape_cookies(jar)
            assert len(parsed) == 1
            assert parsed[0]["name"] == "PHPSESSID"
            assert parsed[0]["value"] == _SECRET

            listing = client.get("/api/platforms")
            assert listing.status_code == 200
            _assert_no_secret(listing.json())
            rostender = next(
                row
                for row in listing.json()["items"]
                if row["platform_id"] == "rostender"
            )
            assert rostender["session"] == "ok"
    finally:
        _cleanup(smoke_db, username=username)

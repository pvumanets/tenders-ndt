"""Unit: Scout auth middleware and login error shape."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.api.main import app

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


@pytest.mark.unit
def test_health_still_public() -> None:
    with _client() as client:
        response = client.get("/api/health")
    assert response.status_code in (200, 503)
    body = response.json()
    assert set(body.keys()) <= {"ok", "db"}
    _assert_no_secrets(body)


@pytest.mark.unit
def test_auth_routes_registered() -> None:
    with _client() as client:
        paths = [getattr(route, "path", "") or "" for route in client.app.routes]
    assert "/api/auth/login" in paths
    assert "/api/auth/logout" in paths
    assert "/api/me" in paths
    assert "/api/inbox" in paths


@pytest.mark.unit
def test_me_and_status_and_inbox_unauthorized_without_cookie() -> None:
    with _client() as client:
        me = client.get("/api/me")
        status = client.get("/api/status")
        inbox = client.get("/api/inbox")
        results = client.get("/api/results")
        start = client.post("/api/run/start", json={})
        stop = client.post("/api/run/stop")
    assert me.status_code == 401
    assert status.status_code == 401
    assert inbox.status_code == 401
    assert results.status_code == 401
    assert start.status_code == 401
    assert stop.status_code == 401
    assert me.json() == {"detail": "unauthorized"}
    assert start.json() == {"detail": "unauthorized"}
    assert stop.json() == {"detail": "unauthorized"}
    _assert_no_secrets(me.json())
    _assert_no_secrets(status.json())
    _assert_no_secrets(inbox.json())
    _assert_no_secrets(start.json())
    _assert_no_secrets(stop.json())


@pytest.mark.unit
def test_login_unknown_and_wrong_same_detail() -> None:
    with _client() as client:
        missing = client.post(
            "/api/auth/login",
            json={"username": "qa_unit_missing", "password": "nope"},
        )
        also_missing = client.post(
            "/api/auth/login",
            json={"username": "qa_unit_also_missing", "password": "other"},
        )
        logout = client.post("/api/auth/logout")
    assert missing.status_code == 401
    assert also_missing.status_code == 401
    assert missing.json() == also_missing.json()
    assert missing.json() == {"detail": "invalid_credentials"}
    _assert_no_secrets(missing.json())
    assert logout.status_code == 204
    assert logout.content == b""

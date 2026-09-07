"""Unit: login rate-limit (087)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api import auth
from app.api.main import app


def _client() -> TestClient:
    try:
        return TestClient(app, lifespan="off")
    except TypeError:
        return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_rate() -> None:
    auth.reset_login_rate_for_tests()
    yield
    auth.reset_login_rate_for_tests()


@pytest.mark.unit
def test_login_rate_limit_returns_429_after_burst(monkeypatch: pytest.MonkeyPatch) -> None:
    # No Postgres in CI: force auth failure without hitting the DB.
    monkeypatch.setattr(auth, "authenticate", lambda *_a, **_k: None)
    with _client() as client:
        for _ in range(auth.LOGIN_FAIL_MAX):
            response = client.post(
                "/api/auth/login",
                json={"username": "qa_unit_missing", "password": "nope"},
            )
            assert response.status_code == 401
            assert response.json() == {"detail": "invalid_credentials"}
        blocked = client.post(
            "/api/auth/login",
            json={"username": "qa_unit_missing", "password": "nope"},
        )
    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "too_many_attempts"}


@pytest.mark.unit
def test_login_rate_limit_counts_database_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_a: object, **_k: object) -> None:
        raise RuntimeError("database_unconfigured")

    monkeypatch.setattr(auth, "authenticate", boom)
    with _client() as client:
        for _ in range(auth.LOGIN_FAIL_MAX):
            assert client.post(
                "/api/auth/login",
                json={"username": "qa_unit_missing", "password": "nope"},
            ).status_code == 401
        blocked = client.post(
            "/api/auth/login",
            json={"username": "qa_unit_missing", "password": "nope"},
        )
    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "too_many_attempts"}


@pytest.mark.unit
def test_client_ip_uses_last_forwarded_hop() -> None:
    class _Req:
        headers = {"x-forwarded-for": "1.1.1.1, 2.2.2.2"}
        client = None

    assert auth.client_ip(_Req()) == "2.2.2.2"  # type: ignore[arg-type]

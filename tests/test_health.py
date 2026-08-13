"""Unit: /api/health does not leak secrets and is not 500 when DB is down."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

_SECRET_NEEDLES = ("password", "postgresql+", "database_url", "cookie")


@pytest.mark.unit
def test_health_no_secrets_and_not_500(api_client: TestClient) -> None:
    response = api_client.get("/api/health")
    assert response.status_code in (200, 503)
    body = response.json()
    assert set(body.keys()) <= {"ok", "db"}
    blob = json.dumps(body).lower()
    for needle in _SECRET_NEEDLES:
        assert needle not in blob


@pytest.mark.smoke
def test_health_200_when_db_up(api_client: TestClient, smoke_db: object) -> None:
    response = api_client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body == {"ok": True, "db": "ok"}
    blob = json.dumps(body).lower()
    for needle in _SECRET_NEEDLES:
        assert needle not in blob

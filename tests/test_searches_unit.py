"""Unit: named searches validation and 401; no database."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.main import app
from app.api.searches import SearchIn


def _client() -> TestClient:
    try:
        return TestClient(app, lifespan="off")
    except TypeError:
        return TestClient(app)


@pytest.mark.unit
def test_search_in_strips_and_rejects_bad_platform() -> None:
    body = SearchIn.model_validate(
        {
            "name": "  РосТендер НК  ",
            "platform_id": "rostender",
            "queries": ["  неразрушающий  ", ""],
            "limit_n": 10,
        }
    )
    assert body.name == "РосТендер НК"
    assert body.queries == ["неразрушающий"]
    with pytest.raises(ValidationError):
        SearchIn.model_validate(
            {"name": "x", "platform_id": "sibur", "queries": ["а"], "limit_n": 10}
        )
    with pytest.raises(ValidationError):
        SearchIn.model_validate(
            {"name": "x", "platform_id": "rostender", "queries": ["  "], "limit_n": 10}
        )


@pytest.mark.unit
def test_searches_unauthorized_without_cookie() -> None:
    with _client() as client:
        assert client.get("/api/searches").status_code == 401
        assert client.post("/api/searches", json={"name": "x"}).status_code == 401
        assert client.put("/api/searches/aaaaaaaa-bbbb-4ccc-8ddd-000000000001", json={}).status_code == 401
        assert client.delete("/api/searches/aaaaaaaa-bbbb-4ccc-8ddd-000000000001").status_code == 401
        assert "/api/searches" in [getattr(route, "path", "") or "" for route in client.app.routes]

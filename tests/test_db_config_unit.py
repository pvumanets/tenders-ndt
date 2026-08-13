"""Unit: host DATABASE_URL fallback from POSTGRES_* — never log secrets."""
from __future__ import annotations

import pytest

from app.db.config import database_url


@pytest.mark.unit
def test_database_url_prefers_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@db:5432/scout")
    monkeypatch.setenv("POSTGRES_PASSWORD", "other")
    assert database_url() == "postgresql+psycopg://u:p@db:5432/scout"


@pytest.mark.unit
def test_database_url_none_without_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("POSTGRES_PASSWORD", "")
    monkeypatch.delenv("SCOUT_TEST_DATABASE_URL", raising=False)
    assert database_url() is None


@pytest.mark.unit
def test_database_url_assembles_host_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("POSTGRES_USER", "scout")
    monkeypatch.setenv("POSTGRES_PASSWORD", "s3cret@x")
    monkeypatch.setenv("POSTGRES_DB", "scout")
    monkeypatch.delenv("POSTGRES_HOST", raising=False)
    monkeypatch.delenv("POSTGRES_PORT", raising=False)
    url = database_url()
    assert url is not None
    assert url.startswith("postgresql+psycopg://")
    assert "@localhost:5433/scout" in url
    assert "s3cret%40x" in url
    assert "s3cret@x@" not in url

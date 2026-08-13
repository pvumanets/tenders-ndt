"""Unit: bootstrap is a no-op without DATABASE_URL."""
from __future__ import annotations

import pytest

from app.db.bootstrap import bootstrap_users


@pytest.mark.unit
def test_bootstrap_noop_without_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("POSTGRES_PASSWORD", "")
    monkeypatch.delenv("SCOUT_TEST_DATABASE_URL", raising=False)
    bootstrap_users()

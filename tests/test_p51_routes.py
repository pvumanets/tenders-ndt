"""Unit: P5.1 routes — /legacy AS-IS; / serves SPA dist when present."""
from __future__ import annotations

from pathlib import Path

import pytest

_LEGACY_MARKER = "ndt-tender-scout — оператор"
_SPA_MARKER = "P51_SPA_MARKER"


@pytest.mark.unit
def test_legacy_serves_as_is_html(api_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCOUT_LEGACY_HTML", "1")
    response = api_client.get("/legacy")
    assert response.status_code == 200
    assert _LEGACY_MARKER in response.text


@pytest.mark.unit
def test_legacy_404_when_disabled(api_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCOUT_LEGACY_HTML", "0")
    response = api_client.get("/legacy")
    assert response.status_code == 404


@pytest.mark.unit
def test_root_serves_spa_when_dist_present(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "index.html").write_text(
        f"<!DOCTYPE html><title>{_SPA_MARKER}</title>",
        encoding="utf-8",
    )
    monkeypatch.setenv("SCOUT_WEB_DIST", str(tmp_path))
    response = api_client.get("/")
    assert response.status_code == 200
    assert _SPA_MARKER in response.text
    assert _LEGACY_MARKER not in response.text

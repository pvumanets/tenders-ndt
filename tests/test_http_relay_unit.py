"""Unit: HTTP egress relay client."""
from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.worker import http_relay


@pytest.mark.unit
def test_relay_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SCOUT_HTTP_RELAY_URL", raising=False)
    monkeypatch.delenv("SCOUT_HTTP_RELAY_SECRET", raising=False)
    assert http_relay.relay_configured() is False
    monkeypatch.setenv("SCOUT_HTTP_RELAY_URL", "https://relay.test:8798")
    monkeypatch.setenv("SCOUT_HTTP_RELAY_SECRET", "secret")
    assert http_relay.relay_configured() is True


@pytest.mark.unit
def test_host_allowed() -> None:
    assert http_relay._host_allowed("https://www.rosatom.rts-tender.ru/market/")
    assert http_relay._host_allowed("https://www.b2b-center.ru/market/")
    assert not http_relay._host_allowed("https://evil.example.test/")


@pytest.mark.unit
def test_assert_relay_endpoint_allowed() -> None:
    http_relay.assert_relay_endpoint_allowed("https://north-hub.example:8798")
    http_relay.assert_relay_endpoint_allowed("http://127.0.0.1:8798")
    http_relay.assert_relay_endpoint_allowed("http://host.docker.internal:8798")
    with pytest.raises(ValueError, match="http_relay_endpoint_insecure"):
        http_relay.assert_relay_endpoint_allowed("http://evil.example:8798")
    with pytest.raises(ValueError, match="http_relay_endpoint_insecure"):
        http_relay.assert_relay_endpoint_allowed("http://10.0.0.5:8798")


@pytest.mark.unit
def test_relay_fetch_builds_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCOUT_HTTP_RELAY_URL", "https://relay.test:8798")
    monkeypatch.setenv("SCOUT_HTTP_RELAY_SECRET", "qa-secret")

    body = b"<html>ok</html>"
    payload = {
        "ok": True,
        "status_code": 200,
        "final_url": "https://www.rosatom.rts-tender.ru/market/",
        "headers": {"content-type": "text/html"},
        "body_b64": base64.b64encode(body).decode("ascii"),
    }

    class FakeResp:
        def __init__(self) -> None:
            self._raw = json.dumps(payload).encode("utf-8")

        def read(self) -> bytes:
            return self._raw

        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> None:
            return None

    fake_urlopen = MagicMock(return_value=FakeResp())
    monkeypatch.setattr(http_relay.urllib.request, "urlopen", fake_urlopen)

    response = http_relay.relay_fetch(
        "GET",
        "https://www.rosatom.rts-tender.ru/market/",
        cookies={"PHPSESSID": "abc"},
    )
    assert response.status_code == 200
    assert response.text == "<html>ok</html>"
    assert fake_urlopen.call_count == 1
    req = fake_urlopen.call_args[0][0]
    assert req.full_url == "https://relay.test:8798/fetch"
    assert req.get_header("Authorization") == "Bearer qa-secret"


@pytest.mark.unit
def test_relay_fetch_rejects_insecure_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCOUT_HTTP_RELAY_URL", "http://evil.example:8798")
    monkeypatch.setenv("SCOUT_HTTP_RELAY_SECRET", "qa-secret")
    with pytest.raises(ValueError, match="http_relay_endpoint_insecure"):
        http_relay.relay_fetch("GET", "https://www.b2b-center.ru/market/")


@pytest.mark.unit
def test_bearer_authorized_compare_digest() -> None:
    path = Path(__file__).resolve().parents[1] / "scripts" / "scout_http_relay_server.py"
    spec = importlib.util.spec_from_file_location("scout_http_relay_server", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.bearer_authorized("Bearer s3cret", "s3cret") is True
    assert mod.bearer_authorized("Bearer wrong", "s3cret") is False
    assert mod.bearer_authorized(None, "s3cret") is False
    assert mod.LISTEN == ("127.0.0.1", 8798)

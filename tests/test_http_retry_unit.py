"""Unit: bounded HTTP retry helper (P14/031)."""
from __future__ import annotations

import httpx
import pytest

from app.worker.http_retry import request_with_retry


class _FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://example.test/x")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("fail", request=request, response=response)


@pytest.mark.unit
def test_request_with_retry_recovers_on_transient_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    retries: list[tuple[int, int]] = []

    def fake_request(self, _method, _url, **kwargs):
        del kwargs
        calls.append(1)
        if len(calls) == 1:
            return _FakeResponse(503)
        return _FakeResponse(200)

    monkeypatch.setattr("app.worker.http_retry.time.sleep", lambda _s: None)
    monkeypatch.setattr(httpx.Client, "request", fake_request)

    with httpx.Client() as client:
        response = request_with_retry(
            client,
            "GET",
            "https://example.test/x",
            on_retry=lambda attempt, code: retries.append((attempt, code)),
        )
    assert response.status_code == 200
    assert len(calls) == 2
    assert retries == [(1, 503)]


@pytest.mark.unit
def test_request_with_retry_raises_after_max_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.worker.http_retry.time.sleep", lambda _s: None)

    def always_500(_self, _method, _url, **kwargs):
        del kwargs
        return _FakeResponse(500)

    monkeypatch.setattr(httpx.Client, "request", always_500)

    with httpx.Client() as client, pytest.raises(httpx.HTTPStatusError):
        request_with_retry(client, "GET", "https://example.test/x", max_attempts=2)

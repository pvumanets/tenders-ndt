"""Unit: fetch allowlist + domain-bound cookies (R1 / 074)."""
from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.worker.fetch_guard import (
    FetchUrlDenied,
    assert_fetch_url_allowed,
    cookies_jar_from_netscape,
    open_allowlisted_stream,
    request_allowlisted,
)


def _write_jar(path: Path, domain: str = "rostender.info") -> Path:
    path.write_text(
        "\n".join(
            [
                "# Netscape HTTP Cookie File",
                f".{domain}\tTRUE\t/\tFALSE\t0\tPHPSESSID\tsecret-session",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


@pytest.mark.unit
def test_assert_fetch_url_allowed_rejects_off_allowlist() -> None:
    with pytest.raises(FetchUrlDenied, match="host_denied"):
        assert_fetch_url_allowed("https://evil.example/steal")


@pytest.mark.unit
def test_assert_fetch_url_allowed_rejects_metadata_ip() -> None:
    with pytest.raises(FetchUrlDenied, match="blocked_ip"):
        assert_fetch_url_allowed("https://169.254.169.254/latest/meta-data/")


@pytest.mark.unit
def test_assert_fetch_url_allowed_rejects_http_wan() -> None:
    with pytest.raises(FetchUrlDenied, match="bad_scheme"):
        assert_fetch_url_allowed("http://rostender.info/x")


@pytest.mark.unit
def test_assert_fetch_url_allowed_accepts_platform_https() -> None:
    assert assert_fetch_url_allowed("https://www.rostender.info/tender/1")


@pytest.mark.unit
def test_cookies_jar_does_not_send_to_evil_host(tmp_path: Path) -> None:
    jar_path = _write_jar(tmp_path / "cookies.txt")
    jar = cookies_jar_from_netscape(jar_path)
    assert jar.get("PHPSESSID", domain="rostender.info") == "secret-session"

    captured: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request.headers.get("cookie"))
        return httpx.Response(200, request=request, text="ok")

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, cookies=jar, follow_redirects=False) as client:
        client.get("https://evil.example/x")
        client.get("https://rostender.info/x")

    assert captured[0] in (None, "")
    assert captured[1] is not None
    assert "PHPSESSID=secret-session" in captured[1]


@pytest.mark.unit
def test_request_allowlisted_rejects_evil_redirect(tmp_path: Path) -> None:
    jar = cookies_jar_from_netscape(_write_jar(tmp_path / "c.txt"))
    hops: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        hops.append(str(request.url))
        if "rostender.info" in str(request.url):
            return httpx.Response(
                302,
                headers={"location": "https://evil.example/steal"},
                request=request,
            )
        return httpx.Response(200, request=request, text="leaked")

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, cookies=jar, follow_redirects=False) as client:
        with pytest.raises(FetchUrlDenied, match="host_denied"):
            request_allowlisted(client, "GET", "https://rostender.info/card")
    assert hops == ["https://rostender.info/card"]


@pytest.mark.unit
def test_open_allowlisted_stream_rejects_off_allowlist() -> None:
    with httpx.Client(follow_redirects=False) as client:
        with pytest.raises(FetchUrlDenied, match="host_denied"):
            open_allowlisted_stream(client, "https://evil.example/doc.pdf")

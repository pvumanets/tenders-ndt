"""HTTP fetch relay for scrape workers when egress IP is captcha-blocked (RTS/B2B).

Uses SCOUT_HTTP_RELAY_URL + SCOUT_HTTP_RELAY_SECRET (north-hub :8798).
"""
from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.request
from urllib.parse import urlparse

import httpx

log = logging.getLogger("uvicorn.error")

_ALLOWED_HOSTS = frozenset(
    {
        "www.b2b-center.ru",
        "b2b-center.ru",
        "www.rosatom.rts-tender.ru",
        "rosatom.rts-tender.ru",
    }
)
_MAX_BODY_BYTES = 8_000_000


def relay_configured() -> bool:
    url = (os.getenv("SCOUT_HTTP_RELAY_URL") or "").strip()
    secret = (os.getenv("SCOUT_HTTP_RELAY_SECRET") or "").strip()
    return bool(url and secret)


def _host_allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    if host in _ALLOWED_HOSTS:
        return True
    return host.endswith(".rts-tender.ru") or host.endswith(".b2b-center.ru")


def relay_fetch(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    content: bytes | None = None,
    timeout: float = 60.0,
) -> httpx.Response:
    """Fetch URL via north-hub relay; returns httpx.Response."""
    if not relay_configured():
        raise RuntimeError("http_relay_unconfigured")
    if not _host_allowed(url):
        raise ValueError("http_relay_host_denied")

    base = (os.getenv("SCOUT_HTTP_RELAY_URL") or "").strip().rstrip("/")
    secret = (os.getenv("SCOUT_HTTP_RELAY_SECRET") or "").strip()
    payload = {
        "url": url,
        "method": method.upper(),
        "headers": headers or {},
        "cookies": cookies or {},
        "body_b64": base64.b64encode(content).decode("ascii") if content else None,
    }
    req = urllib.request.Request(
        f"{base}/fetch",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {secret}",
            "User-Agent": "ndt-tender-scout-http-relay",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout + 15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        log.warning("http_relay_failed: HTTPError_%s", exc.code)
        raise RuntimeError(f"http_relay_http_{exc.code}") from exc
    except Exception as exc:  # noqa: BLE001
        log.warning("http_relay_failed: %s", type(exc).__name__)
        raise RuntimeError("http_relay_failed") from exc

    data = json.loads(raw) if raw else {}
    if not data.get("ok"):
        err = str(data.get("error") or "relay_error")
        raise RuntimeError(f"http_relay_{err}")

    status = int(data.get("status_code") or 0)
    final_url = str(data.get("final_url") or url)
    body_b64 = data.get("body_b64")
    body = base64.b64decode(body_b64) if body_b64 else b""
    if len(body) > _MAX_BODY_BYTES:
        raise RuntimeError("http_relay_body_too_large")

    resp_headers = httpx.Headers(data.get("headers") or {})
    request = httpx.Request(method.upper(), url)
    return httpx.Response(
        status_code=status,
        headers=resp_headers,
        content=body,
        request=request,
        extensions={"final_url": final_url},
    )

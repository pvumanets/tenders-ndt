"""URL allowlist + domain-bound cookies for card/doc fetches (R1 / 074)."""
from __future__ import annotations

import ipaddress
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

from app.worker.cookies import parse_netscape_cookies
from app.worker.http_retry import DEFAULT_PASS_THROUGH_STATUS, request_with_retry

DEFAULT_ALLOW_HOST_SUFFIXES = frozenset(
    {
        "rostender.info",
        "tender.pro",
        "roseltorg.ru",
        "b2b-center.ru",
        "rts-tender.ru",
        "oilb2bcs.ru",
        "sibur.ru",
    }
)
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_REDIRECT_PASS_THROUGH = DEFAULT_PASS_THROUGH_STATUS | REDIRECT_STATUSES
_LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost"})


class FetchUrlDenied(ValueError):
    """URL rejected by fetch allowlist / SSRF guard."""


def allow_hosts() -> frozenset[str]:
    """Platform registry suffixes + optional SCOUT_DOC_FETCH_ALLOW_HOSTS."""
    hosts = set(DEFAULT_ALLOW_HOST_SUFFIXES)
    raw = (os.getenv("SCOUT_DOC_FETCH_ALLOW_HOSTS") or "").strip()
    if raw:
        for part in raw.split(","):
            host = part.strip().lower().lstrip(".")
            if host:
                hosts.add(host)
    return frozenset(hosts)


def host_allowed(host: str, allow: frozenset[str] | None = None) -> bool:
    host = (host or "").lower().rstrip(".")
    if not host:
        return False
    allowed = allow if allow is not None else allow_hosts()
    if host in allowed:
        return True
    for suffix in allowed:
        if host == suffix or host.endswith("." + suffix):
            return True
    return False


def _is_blocked_ip_literal(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def assert_fetch_url_allowed(url: str, allow: frozenset[str] | None = None) -> str:
    """Raise FetchUrlDenied unless URL is https (or http localhost on allowlist)."""
    allowed = allow if allow is not None else allow_hosts()
    raw = (url or "").strip()
    if not raw:
        raise FetchUrlDenied("empty_url")
    parsed = urlparse(raw)
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()
    if not host:
        raise FetchUrlDenied("missing_host")

    is_local = host in _LOCAL_HOSTS
    if is_local:
        if scheme not in {"http", "https"}:
            raise FetchUrlDenied(f"bad_scheme:{scheme or 'none'}")
        if not host_allowed(host, allowed):
            raise FetchUrlDenied(f"host_denied:{host}")
        return raw

    if _is_blocked_ip_literal(host):
        raise FetchUrlDenied(f"blocked_ip:{host}")
    if scheme != "https":
        raise FetchUrlDenied(f"bad_scheme:{scheme or 'none'}")
    if not host_allowed(host, allowed):
        raise FetchUrlDenied(f"host_denied:{host}")
    return raw


def cookies_jar_from_netscape(path: Path) -> httpx.Cookies:
    """Build httpx.Cookies with per-cookie domain (not a bare name→value dict)."""
    jar = httpx.Cookies()
    for item in parse_netscape_cookies(path):
        domain = str(item.get("domain") or "").lstrip(".")
        name = str(item.get("name") or "")
        if not domain or not name:
            continue
        jar.set(
            name,
            str(item.get("value") or ""),
            domain=domain,
            path=str(item.get("path") or "/") or "/",
        )
    return jar


def request_allowlisted(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    allow: frozenset[str] | None = None,
    max_redirects: int = 5,
    **retry_kwargs,
) -> httpx.Response:
    """request_with_retry with allowlist checks on each redirect hop."""
    allowed = allow if allow is not None else allow_hosts()
    current = url
    for _ in range(max_redirects + 1):
        assert_fetch_url_allowed(current, allowed)
        response = request_with_retry(
            client,
            method,
            current,
            pass_through_statuses=_REDIRECT_PASS_THROUGH,
            **retry_kwargs,
        )
        if response.status_code not in REDIRECT_STATUSES:
            return response
        loc = response.headers.get("location")
        if not loc:
            return response
        current = urljoin(str(response.url), loc)
    raise FetchUrlDenied(f"too_many_redirects:{url}")


def open_allowlisted_stream(
    client: httpx.Client,
    url: str,
    *,
    allow: frozenset[str] | None = None,
    max_redirects: int = 5,
) -> httpx.Response:
    """Stream GET with allowlist on each hop. Caller must close the response."""
    allowed = allow if allow is not None else allow_hosts()
    current = url
    for _ in range(max_redirects + 1):
        assert_fetch_url_allowed(current, allowed)
        request = client.build_request("GET", current)
        response = client.send(request, stream=True)
        try:
            if response.status_code not in REDIRECT_STATUSES:
                return response
            loc = response.headers.get("location")
            response.close()
            if not loc:
                raise FetchUrlDenied("redirect_without_location")
            current = urljoin(current, loc)
        except Exception:
            response.close()
            raise
    raise FetchUrlDenied(f"too_many_redirects:{url}")

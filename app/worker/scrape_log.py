"""Structured scrape logs without cookie/secret values (086)."""
from __future__ import annotations

import logging
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

log = logging.getLogger("scout.worker")

_SECRET_KEYS = frozenset(
    {
        "cookie",
        "cookies",
        "token",
        "password",
        "passwd",
        "secret",
        "session",
        "phpsessid",
        "authorization",
        "key",
        "auth",
    }
)


def redact_url(url: str) -> str:
    parts = urlsplit(url or "")
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        folded = key.casefold()
        if folded in _SECRET_KEYS or "cookie" in folded or "token" in folded:
            query.append((key, "REDACTED"))
        else:
            query.append((key, value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def log_fetch(*, platform: str, url: str, status: int | str, parsed_n: int) -> None:
    log.info(
        "scrape platform=%s status=%s parsed_n=%s url=%s",
        platform,
        status,
        parsed_n,
        redact_url(url),
    )

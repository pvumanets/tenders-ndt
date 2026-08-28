"""Bounded HTTP retries for scrape workers (P14/031)."""
from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import httpx

DEFAULT_RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
DEFAULT_BACKOFF = (0.5, 1.5, 3.0)


def request_with_retry(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    max_attempts: int = 3,
    backoff: tuple[float, ...] = DEFAULT_BACKOFF,
    retry_status: frozenset[int] = DEFAULT_RETRY_STATUS,
    on_retry: Callable[[int, int], None] | None = None,
    **kwargs: Any,
) -> httpx.Response:
    """Retry transient HTTP failures; last attempt raises on error status."""
    attempt = 0
    while True:
        attempt += 1
        response = client.request(method, url, **kwargs)
        if response.status_code not in retry_status or attempt >= max_attempts:
            response.raise_for_status()
            return response
        if on_retry:
            on_retry(attempt, response.status_code)
        delay = backoff[min(attempt - 1, len(backoff) - 1)]
        if delay > 0:
            time.sleep(delay)

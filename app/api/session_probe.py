"""TTL cache for live ETP session probes (082 / В2)."""
from __future__ import annotations

import threading
import time

PROBE_TTL_S = 90.0

_lock = threading.Lock()
_cached_at: float = 0.0
_live_calls: int = 0


def reset_for_tests() -> None:
    global _cached_at, _live_calls
    with _lock:
        _cached_at = 0.0
        _live_calls = 0


def live_call_count() -> int:
    with _lock:
        return _live_calls


def note_fresh() -> None:
    """Mark cache warm after an out-of-band live probe (start run, cookie upload)."""
    global _cached_at
    with _lock:
        _cached_at = time.monotonic()


def refresh_session_cached(*, force: bool = False, probe_roseltorg_live: bool = False) -> str:
    from app.api import runner
    from app.api.state import STATE

    global _cached_at, _live_calls
    now = time.monotonic()
    with _lock:
        if not force and _cached_at > 0 and (now - _cached_at) < PROBE_TTL_S:
            return str(STATE.snapshot().get("session") or "unknown")
    result = runner.refresh_session(probe_roseltorg_live=probe_roseltorg_live)
    with _lock:
        _cached_at = time.monotonic()
        _live_calls += 1
    return result

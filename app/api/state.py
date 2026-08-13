"""Thread-safe run status for operator UI."""
from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")


@dataclass
class RunState:
    phase: str = "idle"  # idle|P1|P2|P3|P4|done|error|stopped
    running: bool = False
    stop_requested: bool = False
    list_n: int = 0
    list_limit: int = 1000
    counters: dict[str, int] = field(
        default_factory=lambda: {"L1": 0, "L2": 0, "L3": 0, "noise": 0, "pool": 0}
    )
    cards_done: int = 0
    cards_total: int = 0
    run_dir: str | None = None
    last_error: str | None = None
    session: str = "unknown"  # ok|missing_cookies|expired|unknown
    query: str = "неразрушающий"
    log: deque[dict[str, str]] = field(default_factory=lambda: deque(maxlen=100))
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "phase": self.phase,
                "running": self.running,
                "stop_requested": self.stop_requested,
                "list_n": self.list_n,
                "list_limit": self.list_limit,
                "counters": dict(self.counters),
                "cards_done": self.cards_done,
                "cards_total": self.cards_total,
                "run_dir": self.run_dir,
                "last_error": self.last_error,
                "session": self.session,
                "query": self.query,
                "log": list(self.log),
            }

    def reset_for_run(self, *, limit: int, query: str, run_dir: str) -> None:
        with self._lock:
            self.phase = "P1"
            self.running = True
            self.stop_requested = False
            self.list_n = 0
            self.list_limit = limit
            self.counters = {"L1": 0, "L2": 0, "L3": 0, "noise": 0, "pool": 0}
            self.cards_done = 0
            self.cards_total = 0
            self.run_dir = run_dir
            self.last_error = None
            self.query = query
            self.log.clear()

    def log_msg(self, message: str, *, level: str = "info") -> None:
        with self._lock:
            self.log.append({"t": _now(), "level": level, "msg": message})

    def set_phase(self, phase: str) -> None:
        with self._lock:
            self.phase = phase

    def set_list_progress(self, n: int, limit: int) -> None:
        with self._lock:
            self.list_n = n
            self.list_limit = limit

    def set_counters(self, counters: dict[str, int]) -> None:
        with self._lock:
            self.counters = {
                "L1": counters.get("L1", 0),
                "L2": counters.get("L2", 0),
                "L3": counters.get("L3", 0),
                "noise": counters.get("noise", 0),
                "pool": counters.get("pool", 0),
            }

    def set_cards_progress(self, done: int, total: int) -> None:
        with self._lock:
            self.cards_done = done
            self.cards_total = total

    def request_stop(self) -> None:
        with self._lock:
            self.stop_requested = True

    def should_stop(self) -> bool:
        with self._lock:
            return self.stop_requested

    def finish(self, phase: str = "done", error: str | None = None) -> None:
        with self._lock:
            self.running = False
            self.phase = phase
            if error:
                self.last_error = error
                self.log.append({"t": _now(), "level": "error", "msg": error})

    def set_session(self, session: str) -> None:
        with self._lock:
            self.session = session


STATE = RunState()

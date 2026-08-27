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
    run_report: dict[str, int] = field(
        default_factory=lambda: {"new": 0, "already": 0, "updated": 0, "expired": 0}
    )
    ai_failures: int = 0
    cards_done: int = 0
    cards_total: int = 0
    run_dir: str | None = None
    last_error: str | None = None
    session: str = "unknown"  # rostender: ok|missing_cookies|expired|unknown
    sessions: dict[str, str] = field(default_factory=lambda: {"rostender": "unknown"})
    query: str = ""
    queue: list[dict[str, Any]] = field(default_factory=list)
    queue_index: int = 0
    log: deque[dict[str, str]] = field(default_factory=lambda: deque(maxlen=100))
    _expired_baseline: set[str] = field(default_factory=set, repr=False)
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
                "run_report": dict(self.run_report),
                "ai_failures": self.ai_failures,
                "cards_done": self.cards_done,
                "cards_total": self.cards_total,
                "run_dir": self.run_dir,
                "last_error": self.last_error,
                "session": self.session,
                "sessions": dict(self.sessions),
                "query": self.query,
                "queue": [dict(item) for item in self.queue],
                "queue_index": self.queue_index,
                "queue_total": len(self.queue),
                "current_search_id": self.queue[self.queue_index]["id"]
                if self.queue and 0 <= self.queue_index < len(self.queue)
                else None,
                "current_search_name": self.queue[self.queue_index]["name"]
                if self.queue and 0 <= self.queue_index < len(self.queue)
                else None,
                "log": list(self.log),
            }

    def reset_for_queue(self, *, items: list[dict[str, Any]], run_dir: str) -> None:
        with self._lock:
            self.phase = "P1"
            self.running = True
            self.stop_requested = False
            self.list_n = 0
            self.list_limit = 1000
            self.counters = {"L1": 0, "L2": 0, "L3": 0, "noise": 0, "pool": 0}
            self.run_report = {"new": 0, "already": 0, "updated": 0, "expired": 0}
            self.ai_failures = 0
            self._expired_baseline = set()
            self.cards_done = 0
            self.cards_total = 0
            self.run_dir = run_dir
            self.last_error = None
            self.query = items[0]["name"] if items else ""
            self.queue = [dict(item) for item in items]
            self.queue_index = 0
            self.log.clear()

    def set_expired_baseline(self, ids: set[str]) -> None:
        with self._lock:
            self._expired_baseline = set(ids)

    def add_run_report(
        self,
        *,
        new: int = 0,
        already: int = 0,
        updated: int = 0,
        expired: int | None = None,
    ) -> None:
        with self._lock:
            self.run_report["new"] = self.run_report.get("new", 0) + int(new)
            self.run_report["already"] = self.run_report.get("already", 0) + int(already)
            self.run_report["updated"] = self.run_report.get("updated", 0) + int(updated)
            if expired is not None:
                self.run_report["expired"] = int(expired)

    def finalize_expired_report(self, current_expired: set[str]) -> int:
        with self._lock:
            newly = current_expired - self._expired_baseline
            count = len(newly)
            self.run_report["expired"] = count
            return count

    def set_ai_failures(self, count: int) -> None:
        with self._lock:
            self.ai_failures = int(count)

    def set_queue_index(self, index: int) -> None:
        with self._lock:
            self.queue_index = index
            if 0 <= index < len(self.queue):
                self.query = str(self.queue[index].get("name") or "")
                self.list_n = 0
                self.cards_done = 0
                self.cards_total = 0

    def set_queue_status(self, index: int, status: str) -> None:
        with self._lock:
            if 0 <= index < len(self.queue):
                self.queue[index]["status"] = status

    def cancel_remaining(self, from_index: int) -> None:
        with self._lock:
            for item in self.queue[from_index:]:
                if item.get("status") in {"pending", "running"}:
                    item["status"] = "cancelled"

    def add_counters(self, counters: dict[str, int]) -> None:
        with self._lock:
            for key in ("L1", "L2", "L3", "noise", "pool"):
                self.counters[key] = self.counters.get(key, 0) + int(counters.get(key, 0) or 0)

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

    def set_session(self, session: str, *, platform_id: str = "rostender") -> None:
        with self._lock:
            self.sessions[platform_id] = session
            if platform_id == "rostender":
                self.session = session


STATE = RunState()

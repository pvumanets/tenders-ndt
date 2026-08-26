"""Unit: run queue skip/empty/409; scrape_queries union. No live scrape."""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from app.api import runner
from app.api import searches as searches_api
from app.api.state import STATE
from app.worker.list_scrape import scrape_queries


def _idle_state() -> None:
    STATE.running = False
    STATE.stop_requested = False
    STATE.queue = []
    STATE.queue_index = 0
    STATE.phase = "idle"


@pytest.fixture
def idle_run_state() -> None:
    _idle_state()
    yield
    _idle_state()


@pytest.mark.unit
def test_scrape_queries_union_dedupes_and_caps(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_scrape_list(*, query: str, limit: int, **_kwargs: object) -> list[dict]:
        if query == "a":
            return [{"tender_id": "1", "title": "a1"}, {"tender_id": "2", "title": "a2"}][:limit]
        return [{"tender_id": "2", "title": "b2"}, {"tender_id": "3", "title": "b3"}][:limit]

    monkeypatch.setattr("app.worker.list_scrape.scrape_list", fake_scrape_list)
    rows = scrape_queries(cookies_path=Path("missing.txt"), queries=["a", "b"], limit=10)
    assert [row["tender_id"] for row in rows] == ["1", "2", "3"]
    capped = scrape_queries(cookies_path=Path("missing.txt"), queries=["a", "b"], limit=2)
    assert [row["tender_id"] for row in capped] == ["1", "2"]


@pytest.mark.unit
def test_start_run_empty_queue(monkeypatch: pytest.MonkeyPatch, idle_run_state: None) -> None:
    monkeypatch.setattr(searches_api, "get_queued", lambda: [])
    with pytest.raises(RuntimeError, match="empty_queue"):
        runner.start_run()


@pytest.mark.unit
def test_start_run_already_running(idle_run_state: None) -> None:
    STATE.running = True
    with pytest.raises(RuntimeError, match="already_running"):
        runner.start_run()


@pytest.mark.unit
def test_tender_pro_step_runs_adapter(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(runner, "_run_tender_pro", lambda **_kw: "done")
    status = runner._run_one_search(
        item={
            "id": str(uuid4()),
            "name": "Tender.Pro НК",
            "platform_id": "tender-pro",
            "queries": ["ВИК"],
            "limit_n": 10,
        },
        run_dir=tmp_path,
    )
    assert status == "done"


@pytest.mark.unit
def test_queue_continues_after_tender_pro_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    idle_run_state: None,
) -> None:
    calls: list[str] = []

    def fake_one(*, item: dict, run_dir: Path) -> str:
        calls.append(str(item["platform_id"]))
        return "error" if item["platform_id"] == "tender-pro" else "done"

    monkeypatch.setattr(runner, "_run_one_search", fake_one)
    items = [
        {
            "id": str(uuid4()),
            "name": "Tender.Pro НК",
            "platform_id": "tender-pro",
            "status": "pending",
        },
        {
            "id": str(uuid4()),
            "name": "РосТендер НК",
            "platform_id": "rostender",
            "status": "pending",
        },
    ]
    STATE.reset_for_queue(items=items, run_dir=str(tmp_path))
    runner._run_queue(items=items, run_dir=tmp_path)
    assert calls == ["tender-pro", "rostender"]
    snap = STATE.snapshot()
    assert snap["queue"][0]["status"] == "error"
    assert snap["queue"][1]["status"] == "done"
    assert snap["running"] is False


@pytest.mark.unit
def test_get_queued_empty_when_db_unconfigured(monkeypatch: pytest.MonkeyPatch, idle_run_state: None) -> None:
    monkeypatch.setattr(
        searches_api,
        "get_queued",
        lambda: (_ for _ in ()).throw(RuntimeError("database_unconfigured")),
    )
    with pytest.raises(RuntimeError, match="empty_queue"):
        runner.start_run()

"""Unit: run queue skip/empty/409; scrape_queries union. No live scrape."""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from app.api import runner
from app.api import search_groups as search_groups_api
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
        if int(limit or 0) <= 0:
            limit = 10_000
        if query == "a":
            return [{"tender_id": "1", "title": "a1"}, {"tender_id": "2", "title": "a2"}][:limit]
        return [{"tender_id": "2", "title": "b2"}, {"tender_id": "3", "title": "b3"}][:limit]

    monkeypatch.setattr("app.worker.list_scrape.scrape_list", fake_scrape_list)
    rows = scrape_queries(cookies_path=Path("missing.txt"), queries=["a", "b"], limit=10)
    assert [row["tender_id"] for row in rows] == ["1", "2", "3"]
    capped = scrape_queries(cookies_path=Path("missing.txt"), queries=["a", "b"], limit=2)
    assert [row["tender_id"] for row in capped] == ["1", "2"]
    unlimited = scrape_queries(cookies_path=Path("missing.txt"), queries=["a", "b"], limit=0)
    assert [row["tender_id"] for row in unlimited] == ["1", "2", "3"]


@pytest.mark.unit
def test_start_run_empty_queue(monkeypatch: pytest.MonkeyPatch, idle_run_state: None) -> None:
    monkeypatch.setattr(search_groups_api, "get_queued_steps", lambda: [])
    with pytest.raises(RuntimeError, match="empty_queue"):
        runner.start_run()


@pytest.mark.unit
def test_start_run_already_running(idle_run_state: None) -> None:
    STATE.running = True
    with pytest.raises(RuntimeError, match="already_running"):
        runner.start_run()


@pytest.mark.unit
def test_start_run_sets_pipeline_manual(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    idle_run_state: None,
) -> None:
    monkeypatch.setattr(
        search_groups_api,
        "get_queued_steps",
        lambda: [
            {
                "id": str(uuid4()),
                "name": "НК",
                "platform_id": "rostender",
                "queries": ["ВИК"],
                "limit_n": 0,
            }
        ],
    )
    monkeypatch.setattr(runner, "refresh_session", lambda: "ok")
    monkeypatch.setattr(runner, "_repo_root", lambda: tmp_path)

    class IdleThread:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def start(self) -> None:
            return None

    monkeypatch.setattr(runner.threading, "Thread", IdleThread)
    assert runner.start_run() is True
    snap = STATE.snapshot()
    assert snap["pipeline"] == "manual"
    assert snap["running"] is True
    STATE.finish("done")


@pytest.mark.unit
def test_start_run_ticker_skips_already_running_without_raise(
    monkeypatch: pytest.MonkeyPatch, idle_run_state: None
) -> None:
    skipped: list[str] = []
    monkeypatch.setattr(
        "app.api.schedule.record_slot_skip",
        lambda reason, **_k: skipped.append(reason),
    )
    STATE.running = True
    assert runner.start_run(pipeline="auto", from_ticker=True) is False
    assert skipped == ["already_running"]


@pytest.mark.unit
def test_start_run_ticker_empty_queue_without_raise(
    monkeypatch: pytest.MonkeyPatch, idle_run_state: None
) -> None:
    skipped: list[str] = []
    monkeypatch.setattr(search_groups_api, "get_queued_steps", lambda: [])
    monkeypatch.setattr(
        "app.api.schedule.record_slot_skip",
        lambda reason, **_k: skipped.append(reason),
    )
    assert runner.start_run(pipeline="auto", from_ticker=True) is False
    assert skipped == ["empty_queue"]


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
    assert snap["phase"] == "partial"


@pytest.mark.unit
def test_auto_queue_keeps_running_during_ai(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    idle_run_state: None,
) -> None:
    seen_running: list[bool] = []

    def fake_ai(_prefer: set[str]) -> dict:
        seen_running.append(bool(STATE.snapshot()["running"]))
        return {"processed": 0, "failed": 0, "items": []}

    monkeypatch.setattr(runner, "_run_one_search", lambda **_kw: "done")
    monkeypatch.setattr("app.api.inbox.run_auto_ai_review", fake_ai)
    items = [
        {
            "id": str(uuid4()),
            "name": "РосТендер НК",
            "platform_id": "rostender",
            "status": "pending",
        },
    ]
    STATE.reset_for_queue(items=items, run_dir=str(tmp_path), pipeline="auto")
    runner._run_queue(items=items, run_dir=tmp_path, pipeline="auto")
    assert seen_running == [True]
    snap = STATE.snapshot()
    assert snap["running"] is False
    assert snap["phase"] == "done"


@pytest.mark.unit
def test_start_run_clears_running_if_thread_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    idle_run_state: None,
) -> None:
    monkeypatch.setattr(
        search_groups_api,
        "get_queued_steps",
        lambda: [{"id": str(uuid4()), "name": "НК", "platform_id": "rostender"}],
    )
    monkeypatch.setattr(runner, "refresh_session", lambda: "ok")
    monkeypatch.setattr(runner, "_repo_root", lambda: tmp_path)

    class BoomThread:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("thread_failed")

    monkeypatch.setattr(runner.threading, "Thread", BoomThread)
    with pytest.raises(RuntimeError, match="thread_failed"):
        runner.start_run()
    assert STATE.snapshot()["running"] is False
    assert STATE.snapshot()["phase"] == "error"


@pytest.mark.unit
def test_soft_stop_after_p2_ingests_board_rows(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    ingested: list[dict] = []
    real_score = runner.score_rows

    def score_and_request_stop(rows: list[dict]):
        scored, summary, card_ids = real_score(rows)
        monkeypatch.setattr(runner.STATE, "should_stop", lambda: True)
        return scored, summary, card_ids

    monkeypatch.setattr(runner, "probe_rostender_cookies", lambda *_a, **_k: "ok")
    monkeypatch.setattr(
        runner,
        "scrape_queries",
        lambda **_kw: [{"tender_id": "99", "title": "Проведение неразрушающего контроля сварных швов"}],
    )
    monkeypatch.setattr(runner, "score_rows", score_and_request_stop)
    def no_enrich(*_a, **_k):
        raise AssertionError("P3 must not run")

    monkeypatch.setattr(runner, "enrich_cards", no_enrich)
    monkeypatch.setattr(runner, "_ingest_step", lambda **kw: ingested.append(kw))
    monkeypatch.setattr(runner, "_cookies_path", lambda _p: tmp_path / "cookies.txt")
    (tmp_path / "cookies.txt").write_text("dummy", encoding="utf-8")

    status = runner._run_rostender(
        item={
            "id": str(uuid4()),
            "name": "test",
            "platform_id": "rostender",
            "queries": ["узк"],
            "limit_n": 0,
        },
        run_dir=tmp_path,
    )
    assert status == "cancelled"
    assert ingested
    board = ingested[-1]["rows"]
    assert board
    assert board[0]["tier"] in {"L1", "L2", "L3"}


@pytest.mark.unit
def test_get_queued_empty_when_db_unconfigured(monkeypatch: pytest.MonkeyPatch, idle_run_state: None) -> None:
    monkeypatch.setattr(
        search_groups_api,
        "get_queued_steps",
        lambda: (_ for _ in ()).throw(RuntimeError("database_unconfigured")),
    )
    with pytest.raises(RuntimeError, match="empty_queue"):
        runner.start_run()

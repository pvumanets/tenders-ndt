"""Background P1–P4 runner for operator UI — queue of named searches (023)."""
from __future__ import annotations

import json
import os
import threading
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

from app.api import searches as searches_api
from app.api.state import STATE
from app.scoring.pipeline import score_rows
from app.worker.artifacts import write_artifacts
from app.worker.card_scrape import enrich_cards
from app.worker.docs import download_docs_enabled, download_inbox_docs
from app.worker.ingest import ingest_run, redact_db_error
from app.worker.list_scrape import AuthError, scrape_queries

_thread: threading.Thread | None = None
_lock = threading.Lock()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _cookies_path() -> Path:
    load_dotenv(_repo_root() / ".env")
    p = Path(os.getenv("ROSTENDER_COOKIES_FILE", "./cookies.rostender.txt"))
    if not p.is_absolute():
        p = _repo_root() / p
    return p


def refresh_session() -> str:
    p = _cookies_path()
    if not p.is_file():
        STATE.set_session("missing_cookies")
        STATE.set_session("ok", platform_id="tender-pro")
        return "missing_cookies"
    STATE.set_session("ok")
    STATE.set_session("ok", platform_id="tender-pro")
    return "ok"


def start_run() -> None:
    global _thread
    with _lock:
        if STATE.snapshot()["running"]:
            raise RuntimeError("already_running")
        try:
            queued = searches_api.get_queued()
        except RuntimeError as exc:
            if str(exc) == "database_unconfigured":
                raise RuntimeError("empty_queue") from exc
            raise
        if not queued:
            raise RuntimeError("empty_queue")
        refresh_session()
        run_dir = _repo_root() / "runs" / date.today().isoformat()
        run_dir.mkdir(parents=True, exist_ok=True)
        items = [
            {
                "id": str(row.id),
                "name": row.name,
                "platform_id": row.platform_id,
                "queries": list(row.queries or []),
                "limit_n": row.limit_n,
                "status": "pending",
            }
            for row in queued
        ]
        STATE.reset_for_queue(items=items, run_dir=str(run_dir))
        STATE.log_msg(f"Queue: {len(items)} search(es)")
        _thread = threading.Thread(
            target=_run_queue,
            kwargs={"items": items, "run_dir": run_dir},
            daemon=True,
        )
        _thread.start()


def request_stop() -> None:
    STATE.request_stop()
    STATE.log_msg("Stop requested (soft)", level="warn")


def _query_label(item: dict) -> str:
    name = str(item.get("name") or "")
    queries = item.get("queries") or []
    joined = ", ".join(str(q) for q in queries)
    return f"{name}: {joined}" if joined else name


def _ingest_step(
    *,
    item: dict,
    status: str,
    rows: list[dict],
    started_at: datetime,
    error: str | None = None,
) -> None:
    search_id: UUID | None = None
    raw_id = item.get("id")
    if raw_id:
        try:
            search_id = UUID(str(raw_id))
        except ValueError:
            search_id = None
    try:
        result = ingest_run(
            query=_query_label(item),
            limit_n=int(item.get("limit_n") or 1000),
            status=status,
            rows=rows,
            started_at=started_at,
            source_platform_id=str(item.get("platform_id") or "rostender"),
            search_id=search_id,
        )
        if result is None:
            STATE.log_msg("Ingest skipped (database unconfigured)", level="warn")
        else:
            STATE.log_msg(f"Ingest: {result.lot_count} lots (score≥4)")
    except Exception as exc:  # noqa: BLE001
        ingest_error = f"IngestError: {redact_db_error(exc)}"
        STATE.log_msg(ingest_error, level="error")
        if error:
            STATE.log_msg(error, level="error")


def _download_docs(rows: list[dict]) -> None:
    if not download_docs_enabled():
        STATE.log_msg("Docs: skip (DOWNLOAD_DOCS=0)")
        return
    if not rows:
        return
    STATE.log_msg("Docs: downloading score≥4…")
    try:
        result = download_inbox_docs(
            rows,
            cookies_path=_cookies_path(),
            delay_s=0.2,
            should_stop=STATE.should_stop,
        )
        STATE.log_msg(
            f"Docs: saved={result.saved} skipped={result.skipped} errors={result.errors}"
        )
    except AuthError as exc:
        STATE.set_session("expired")
        STATE.log_msg(f"Docs AuthError: {exc}", level="error")
    except Exception as exc:  # noqa: BLE001
        STATE.log_msg(f"Docs error: {type(exc).__name__}: {exc}", level="error")


def _run_queue(*, items: list[dict], run_dir: Path) -> None:
    overall = "done"
    try:
        for index, item in enumerate(items):
            if STATE.should_stop():
                STATE.cancel_remaining(index)
                overall = "stopped"
                STATE.log_msg("Queue stopped; remaining cancelled", level="warn")
                break
            STATE.set_queue_index(index)
            STATE.set_queue_status(index, "running")
            STATE.log_msg(f"Search {index + 1}/{len(items)}: {item['name']}")
            step_status = _run_one_search(item=item, run_dir=run_dir)
            STATE.set_queue_status(index, step_status)
            if STATE.should_stop():
                STATE.cancel_remaining(index + 1)
                overall = "stopped"
                break
            if step_status == "error" and overall != "stopped":
                overall = "done"
        else:
            if overall == "done":
                STATE.log_msg("Queue finished")
    except Exception as exc:  # noqa: BLE001
        overall = "error"
        STATE.log_msg(f"{type(exc).__name__}: {exc}", level="error")
        STATE.finish("error", error=f"{type(exc).__name__}: {exc}")
        return
    STATE.finish(overall)


def _run_one_search(*, item: dict, run_dir: Path) -> str:
    platform = str(item.get("platform_id") or "")
    if platform == "tender-pro":
        STATE.log_msg("Tender.Pro adapter not in this ship (024) — skip", level="warn")
        _ingest_step(
            item=item,
            status="skipped",
            rows=[],
            started_at=datetime.now(timezone.utc),
        )
        return "skipped"
    if platform != "rostender":
        STATE.log_msg(f"No adapter for {platform} — skip", level="warn")
        _ingest_step(
            item=item,
            status="skipped",
            rows=[],
            started_at=datetime.now(timezone.utc),
        )
        return "skipped"
    return _run_rostender(item=item, run_dir=run_dir)


def _run_rostender(*, item: dict, run_dir: Path) -> str:
    cookies = _cookies_path()
    if not cookies.is_file():
        STATE.set_session("missing_cookies")
        STATE.log_msg("Rostender cookies missing — skip step", level="warn")
        _ingest_step(
            item=item,
            status="skipped",
            rows=[],
            started_at=datetime.now(timezone.utc),
        )
        return "skipped"
    base = os.getenv("ROSTENDER_BASE_URL", "https://rostender.info")
    queries = [str(q) for q in (item.get("queries") or []) if str(q).strip()]
    limit = int(item.get("limit_n") or 1000)
    started_at = datetime.now(timezone.utc)
    enriched: list[dict] = []
    status = "done"
    try:
        STATE.set_phase("P1")
        STATE.log_msg("P1: list scrape…")
        rows = scrape_queries(
            cookies_path=cookies,
            base_url=base,
            queries=queries,
            limit=limit,
            should_stop=STATE.should_stop,
            on_progress=lambda n, lim: STATE.set_list_progress(n, lim),
        )
        (run_dir / "raw-list.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        STATE.set_list_progress(len(rows), limit)
        STATE.log_msg(f"P1 done: {len(rows)} rows")
        if STATE.should_stop():
            STATE.log_msg("Stopped after P1", level="warn")
            _ingest_step(item=item, status="stopped", rows=[], started_at=started_at)
            return "cancelled"

        STATE.set_phase("P2")
        STATE.log_msg("P2: scoring…")
        scored, summary, card_ids = score_rows(rows)
        STATE.add_counters(summary)
        (run_dir / "scored-list.json").write_text(
            json.dumps(scored, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (run_dir / "tier-summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (run_dir / "card-ids.json").write_text(
            json.dumps(card_ids, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        STATE.set_cards_progress(0, len(card_ids))
        STATE.log_msg(f"P2 done: tiers={summary} cards={len(card_ids)}")
        if STATE.should_stop():
            STATE.log_msg("Stopped after P2", level="warn")
            _ingest_step(item=item, status="stopped", rows=[], started_at=started_at)
            return "cancelled"

        STATE.set_phase("P3")
        STATE.log_msg("P3: fetching cards…")
        enriched, errors = enrich_cards(
            scored,
            card_ids,
            cookies_path=cookies,
            delay_s=0.2,
            should_stop=STATE.should_stop,
            on_progress=lambda d, t: STATE.set_cards_progress(d, t),
        )
        (run_dir / "scored-list.json").write_text(
            json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (run_dir / "cards-errors.json").write_text(
            json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        STATE.log_msg(f"P3 done: errors={len(errors)}")
        if STATE.should_stop():
            STATE.set_phase("P4")
            write_artifacts(run_dir, enriched)
            STATE.log_msg("Stopped during/after P3; partial artifacts written", level="warn")
            _ingest_step(item=item, status="stopped", rows=enriched, started_at=started_at)
            _download_docs(enriched)
            return "cancelled"

        STATE.set_phase("P4")
        STATE.log_msg("P4: artifacts…")
        write_artifacts(run_dir, enriched)
        readme = run_dir / "README.md"
        readme.write_text(
            f"# Run {run_dir.name}\n\n**status:** ok\n\n**via:** operator UI\n\n"
            f"**search:** {item.get('name')}\n\n**query:** {_query_label(item)}\n\n"
            f"**limit:** {limit}\n\n"
            f"**tiers:** {summary}\n\n"
            f"**files:** raw-list, scored-list, tenders.csv, tenders.md, priority-fit.md\n",
            encoding="utf-8",
        )
        STATE.log_msg(f"P4 done → {run_dir}")
        _ingest_step(item=item, status="done", rows=enriched, started_at=started_at)
        _download_docs(enriched)
        return "done"
    except AuthError as e:
        STATE.set_session("expired")
        status = "error"
        _ingest_step(
            item=item,
            status="error",
            rows=enriched,
            started_at=started_at,
            error=f"AuthError: {e}",
        )
        STATE.log_msg(f"AuthError: {e}", level="error")
        return status
    except Exception as e:  # noqa: BLE001
        _ingest_step(
            item=item,
            status="error",
            rows=enriched,
            started_at=started_at,
            error=f"{type(e).__name__}: {e}",
        )
        STATE.log_msg(f"{type(e).__name__}: {e}", level="error")
        return "error"

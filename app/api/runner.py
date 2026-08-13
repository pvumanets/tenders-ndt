"""Background P1–P4 runner for operator UI."""
from __future__ import annotations

import json
import os
import threading
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from app.api.state import STATE
from app.scoring.pipeline import score_rows
from app.worker.artifacts import write_artifacts
from app.worker.card_scrape import enrich_cards
from app.worker.docs import download_docs_enabled, download_inbox_docs
from app.worker.ingest import ingest_run, redact_db_error
from app.worker.list_scrape import AuthError, scrape_list

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
        return "missing_cookies"
    STATE.set_session("ok")
    return "ok"


def start_run(*, limit: int = 1000, query: str = "неразрушающий") -> None:
    global _thread
    with _lock:
        if STATE.snapshot()["running"]:
            raise RuntimeError("already_running")
        refresh_session()
        if STATE.snapshot()["session"] == "missing_cookies":
            raise RuntimeError("missing_cookies")
        run_dir = _repo_root() / "runs" / date.today().isoformat()
        run_dir.mkdir(parents=True, exist_ok=True)
        STATE.reset_for_run(limit=limit, query=query, run_dir=str(run_dir))
        STATE.log_msg(f"Start limit={limit} query={query}")
        _thread = threading.Thread(
            target=_run_pipeline,
            kwargs={"limit": limit, "query": query, "run_dir": run_dir},
            daemon=True,
        )
        _thread.start()


def request_stop() -> None:
    STATE.request_stop()
    STATE.log_msg("Stop requested (soft)", level="warn")


def _ingest_and_finish(
    *,
    query: str,
    limit: int,
    status: str,
    rows: list[dict],
    started_at: datetime,
    error: str | None = None,
) -> None:
    try:
        result = ingest_run(
            query=query,
            limit_n=limit,
            status=status,
            rows=rows,
            started_at=started_at,
        )
        if result is None:
            STATE.log_msg("Ingest skipped (database unconfigured)", level="warn")
        else:
            STATE.log_msg(f"Ingest: {result.lot_count} lots (score≥4)")
    except Exception as exc:  # noqa: BLE001
        ingest_error = f"IngestError: {redact_db_error(exc)}"
        STATE.log_msg(ingest_error, level="error")
        if status != "error":
            status = "error"
        error = f"{error}; {ingest_error}" if error else ingest_error
    _download_docs(rows)
    STATE.finish(status, error=error)


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


def _run_pipeline(*, limit: int, query: str, run_dir: Path) -> None:
    cookies = _cookies_path()
    base = os.getenv("ROSTENDER_BASE_URL", "https://rostender.info")
    started_at = datetime.now(timezone.utc)
    enriched: list[dict] = []
    try:
        # P1
        STATE.set_phase("P1")
        STATE.log_msg("P1: list scrape…")
        rows = scrape_list(
            cookies_path=cookies,
            base_url=base,
            query=query,
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
            _ingest_and_finish(
                query=query, limit=limit, status="stopped", rows=[], started_at=started_at
            )
            return

        # P2
        STATE.set_phase("P2")
        STATE.log_msg("P2: scoring…")
        scored, summary, card_ids = score_rows(rows)
        STATE.set_counters(summary)
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
            _ingest_and_finish(
                query=query, limit=limit, status="stopped", rows=[], started_at=started_at
            )
            return

        # P3
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
            # still write partial artifacts
            STATE.set_phase("P4")
            write_artifacts(run_dir, enriched)
            STATE.log_msg("Stopped during/after P3; partial artifacts written", level="warn")
            _ingest_and_finish(
                query=query,
                limit=limit,
                status="stopped",
                rows=enriched,
                started_at=started_at,
            )
            return

        # P4
        STATE.set_phase("P4")
        STATE.log_msg("P4: artifacts…")
        write_artifacts(run_dir, enriched)
        readme = run_dir / "README.md"
        readme.write_text(
            f"# Run {run_dir.name}\n\n**status:** ok\n\n**via:** operator UI\n\n"
            f"**query:** {query}\n\n**limit:** {limit}\n\n"
            f"**tiers:** {summary}\n\n"
            f"**files:** raw-list, scored-list, tenders.csv, tenders.md, priority-fit.md\n",
            encoding="utf-8",
        )
        STATE.log_msg(f"P4 done → {run_dir}")
        _ingest_and_finish(
            query=query, limit=limit, status="done", rows=enriched, started_at=started_at
        )
    except AuthError as e:
        STATE.set_session("expired")
        _ingest_and_finish(
            query=query,
            limit=limit,
            status="error",
            rows=enriched,
            started_at=started_at,
            error=f"AuthError: {e}",
        )
    except Exception as e:  # noqa: BLE001
        _ingest_and_finish(
            query=query,
            limit=limit,
            status="error",
            rows=enriched,
            started_at=started_at,
            error=f"{type(e).__name__}: {e}",
        )

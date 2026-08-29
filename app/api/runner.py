"""Background P1–P4 runner for operator UI — queue of named searches (023/024)."""
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
from app.scoring.pipeline import rescore_rows, score_rows
from app.worker import roseltorg as roseltorg_worker
from app.worker import tender_pro as tender_pro_worker
from app.worker.artifacts import write_artifacts
from app.worker.card_scrape import enrich_cards
from app.worker.docs import download_docs_enabled, download_inbox_docs
from app.worker.ingest import ingest_run, redact_db_error, snapshot_expired_tender_ids
from app.worker.list_scrape import AuthError, probe_rostender_cookies, scrape_queries
from app.worker.platform_ids import (
    PLATFORM_ROSELTORG,
    PLATFORM_ROSTENDER,
    PLATFORM_TENDER_PRO,
    prefix_rows,
)

_thread: threading.Thread | None = None
_lock = threading.Lock()
_BAD_STEP = frozenset({"skipped", "error", "cancelled"})
_BOARD_TIERS = frozenset({"L1", "L2", "L3"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _cookies_path(platform_id: str = PLATFORM_ROSTENDER) -> Path:
    load_dotenv(_repo_root() / ".env")
    if platform_id == PLATFORM_TENDER_PRO:
        raw = os.getenv("TENDER_PRO_COOKIES_FILE", "./cookies.tender-pro.txt")
    elif platform_id == PLATFORM_ROSELTORG:
        raw = os.getenv("ROSELTORG_COOKIES_FILE", "./cookies.roseltorg.txt")
    else:
        raw = os.getenv("ROSTENDER_COOKIES_FILE", "./cookies.rostender.txt")
    path = Path(raw)
    if not path.is_absolute():
        path = _repo_root() / path
    return path


def _http_retry_callback(attempt: int, status_code: int) -> None:
    STATE.add_http_retry()
    STATE.log_msg(f"HTTP retry #{attempt} (status {status_code})", level="warn")


def _board_rows(scored: list[dict]) -> list[dict]:
    return [row for row in scored if str(row.get("tier") or "") in _BOARD_TIERS]


def _apply_rescore_counter_delta(old: dict, new: dict) -> None:
    delta: dict[str, int] = {}
    for key in ("L1", "L2", "L3", "noise", "pool"):
        diff = int(new.get(key, 0) or 0) - int(old.get(key, 0) or 0)
        if diff:
            delta[key] = diff
    if delta:
        STATE.add_counters(delta)


def _write_scored_bundle(run_dir: Path, rows: list[dict], summary: dict, card_ids: list[str]) -> None:
    (run_dir / "scored-list.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "tier-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "card-ids.json").write_text(
        json.dumps(card_ids, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def refresh_session(*, probe_roseltorg_live: bool = True) -> str:
    rostender = _cookies_path(PLATFORM_ROSTENDER)
    base = os.getenv("ROSTENDER_BASE_URL", "https://rostender.info")
    probe = probe_rostender_cookies(rostender, base, on_retry=_http_retry_callback)
    if probe == "missing":
        STATE.set_session("missing_cookies")
    elif probe == "expired":
        STATE.set_session("expired")
    else:
        STATE.set_session("ok")

    tp_cookies = _cookies_path(PLATFORM_TENDER_PRO)
    tp_base = os.getenv("TENDER_PRO_BASE_URL", tender_pro_worker.DEFAULT_BASE)
    tp_probe = tender_pro_worker.probe_tender_pro_cookies(
        tp_cookies, tp_base, on_retry=_http_retry_callback
    )
    if tp_probe == "missing":
        STATE.set_session("missing_cookies", platform_id=PLATFORM_TENDER_PRO)
    elif tp_probe == "expired":
        STATE.set_session("expired", platform_id=PLATFORM_TENDER_PRO)
    else:
        STATE.set_session("ok", platform_id=PLATFORM_TENDER_PRO)

    re_cookies = _cookies_path(PLATFORM_ROSELTORG)
    re_base = os.getenv("ROSELTORG_BASE_URL", roseltorg_worker.DEFAULT_BASE)
    if not roseltorg_worker.cookies_present():
        STATE.set_session("missing_cookies", platform_id=PLATFORM_ROSELTORG)
    elif probe_roseltorg_live:
        re_probe = roseltorg_worker.probe_roseltorg_session(
            cookies_file=re_cookies,
            base=re_base,
            on_retry=_http_retry_callback,
        )
        if re_probe == "missing":
            STATE.set_session("missing_cookies", platform_id=PLATFORM_ROSELTORG)
        elif re_probe == "expired":
            STATE.set_session("expired", platform_id=PLATFORM_ROSELTORG)
        else:
            STATE.set_session("ok", platform_id=PLATFORM_ROSELTORG)
    return STATE.snapshot()["session"]


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
                "exclude": list(row.exclude or []),
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
            limit_n=int(item.get("limit_n") or 0),
            status=status,
            rows=rows,
            started_at=started_at,
            source_platform_id=str(item.get("platform_id") or PLATFORM_ROSTENDER),
            search_id=search_id,
        )
        if result is None:
            STATE.log_msg("Ingest skipped (database unconfigured)", level="warn")
        else:
            STATE.add_run_report(
                new=result.new_count,
                already=result.already_count,
                updated=result.updated_count,
            )
            STATE.log_msg(
                "Ingest: "
                f"{result.lot_count} lots (L1–L3); "
                f"новые={result.new_count}, "
                f"уже были={result.already_count}, "
                f"обновлено={result.updated_count}"
            )
    except Exception as exc:  # noqa: BLE001
        ingest_error = f"IngestError: {redact_db_error(exc)}"
        STATE.log_msg(ingest_error, level="error")
        if error:
            STATE.log_msg(error, level="error")


def _download_docs(rows: list[dict], *, platform_id: str) -> None:
    if not download_docs_enabled():
        STATE.log_msg("Docs: skip (DOWNLOAD_DOCS=0)")
        return
    if not rows:
        return
    cookies = _cookies_path(platform_id)
    if platform_id == PLATFORM_ROSELTORG and not cookies.is_file():
        STATE.log_msg("Docs: Росэлторг cookies missing — skip files", level="warn")
        return
    if platform_id == PLATFORM_TENDER_PRO and not cookies.is_file():
        STATE.log_msg("Docs: Tender.Pro cookies missing — skip files", level="warn")
        return
    if platform_id == PLATFORM_ROSTENDER and not cookies.is_file():
        STATE.log_msg("Docs: rostender cookies missing — skip files", level="warn")
        return
    STATE.log_msg("Docs: downloading L1–L3…")
    try:
        result = download_inbox_docs(
            rows,
            cookies_path=cookies,
            delay_s=0.2,
            should_stop=STATE.should_stop,
        )
        STATE.log_msg(
            f"Docs: saved={result.saved} skipped={result.skipped} errors={result.errors}"
        )
    except AuthError as exc:
        if platform_id == PLATFORM_ROSTENDER:
            STATE.set_session("expired")
        else:
            STATE.set_session("expired", platform_id=PLATFORM_TENDER_PRO)
        STATE.log_msg(f"Docs AuthError: {exc}", level="error")
    except Exception as exc:  # noqa: BLE001
        STATE.log_msg(f"Docs error: {type(exc).__name__}: {exc}", level="error")


def _run_queue(*, items: list[dict], run_dir: Path) -> None:
    overall = "done"
    try:
        baseline = snapshot_expired_tender_ids()
        STATE.set_expired_baseline(baseline)
        STATE.log_msg(f"Expired baseline: {len(baseline)} lot(s)")
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
            if step_status in _BAD_STEP and overall != "stopped":
                overall = "partial"
        else:
            if overall == "done":
                STATE.log_msg("Queue finished")
            elif overall == "partial":
                STATE.log_msg("Queue finished (partial)", level="warn")
        newly_expired = STATE.finalize_expired_report(snapshot_expired_tender_ids())
        STATE.log_msg(f"Ушли в просроченные: {newly_expired}")
    except Exception as exc:  # noqa: BLE001
        overall = "error"
        STATE.log_msg(f"{type(exc).__name__}: {exc}", level="error")
        STATE.finish("error", error=f"{type(exc).__name__}: {exc}")
        return
    STATE.finish(overall)


def _run_one_search(*, item: dict, run_dir: Path) -> str:
    platform = str(item.get("platform_id") or "")
    if platform == PLATFORM_TENDER_PRO:
        return _run_tender_pro(item=item, run_dir=run_dir)
    if platform == PLATFORM_ROSELTORG:
        return _run_roseltorg(item=item, run_dir=run_dir)
    if platform == PLATFORM_ROSTENDER:
        return _run_rostender(item=item, run_dir=run_dir)
    STATE.log_msg(f"No adapter for {platform} — skip", level="warn")
    _ingest_step(
        item=item,
        status="skipped",
        rows=[],
        started_at=datetime.now(timezone.utc),
    )
    return "skipped"


def _finish_artifacts(
    *,
    item: dict,
    run_dir: Path,
    enriched: list[dict],
    summary: dict,
    limit: int,
    started_at: datetime,
    platform_id: str,
    status: str = "done",
) -> str:
    write_artifacts(run_dir, enriched)
    readme = run_dir / "README.md"
    readme.write_text(
        f"# Run {run_dir.name}\n\n**status:** {status}\n\n**via:** operator UI\n\n"
        f"**platform:** {platform_id}\n\n"
        f"**search:** {item.get('name')}\n\n**query:** {_query_label(item)}\n\n"
        f"**limit:** {limit}\n\n"
        f"**tiers:** {summary}\n\n"
        f"**files:** raw-list, scored-list, tenders.csv, tenders.md, priority-fit.md\n",
        encoding="utf-8",
    )
    STATE.log_msg(f"P4 done → {run_dir}")
    _ingest_step(item=item, status=status, rows=enriched, started_at=started_at)
    _download_docs(enriched, platform_id=platform_id)
    return "done" if status == "done" else status


def _run_rostender(*, item: dict, run_dir: Path) -> str:
    cookies = _cookies_path(PLATFORM_ROSTENDER)
    base = os.getenv("ROSTENDER_BASE_URL", "https://rostender.info")
    probe = probe_rostender_cookies(cookies, base, on_retry=_http_retry_callback)
    if probe != "ok":
        if probe == "missing":
            STATE.set_session("missing_cookies")
        else:
            STATE.set_session("expired")
        STATE.log_msg("Rostender session not ok — skip step", level="warn")
        _ingest_step(
            item=item,
            status="skipped",
            rows=[],
            started_at=datetime.now(timezone.utc),
        )
        return "skipped"
    queries = [str(q) for q in (item.get("queries") or []) if str(q).strip()]
    exclude = [str(x) for x in (item.get("exclude") or []) if str(x).strip()]
    limit = int(item.get("limit_n") or 0)
    started_at = datetime.now(timezone.utc)
    enriched: list[dict] = []
    summary: dict = {}
    try:
        STATE.set_phase("P1")
        STATE.log_msg("P1: list scrape…")
        rows = scrape_queries(
            cookies_path=cookies,
            base_url=base,
            queries=queries,
            limit=limit,
            exclude=exclude,
            should_stop=STATE.should_stop,
            on_retry=_http_retry_callback,
            on_progress=lambda n, lim: STATE.set_list_progress(n, lim),
        )
        rows = prefix_rows(rows, PLATFORM_ROSTENDER)
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
            _ingest_step(
                item=item,
                status="stopped",
                rows=_board_rows(scored),
                started_at=started_at,
            )
            return "cancelled"

        STATE.set_phase("P3")
        STATE.log_msg("P3: fetching cards…")
        enriched, errors = enrich_cards(
            scored,
            card_ids,
            cookies_path=cookies,
            delay_s=0.2,
            should_stop=STATE.should_stop,
            on_retry=_http_retry_callback,
            on_progress=lambda d, t: STATE.set_cards_progress(d, t),
        )
        old_summary = dict(summary)
        enriched, summary, card_ids = rescore_rows(enriched)
        _apply_rescore_counter_delta(old_summary, summary)
        _write_scored_bundle(run_dir, enriched, summary, card_ids)
        (run_dir / "cards-errors.json").write_text(
            json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        STATE.log_msg(f"P3 done: errors={len(errors)}; re-score tiers={summary}")
        if STATE.should_stop():
            STATE.set_phase("P4")
            write_artifacts(run_dir, enriched)
            STATE.log_msg("Stopped during/after P3; partial artifacts written", level="warn")
            _ingest_step(
                item=item,
                status="stopped",
                rows=_board_rows(enriched),
                started_at=started_at,
            )
            _download_docs(enriched, platform_id=PLATFORM_ROSTENDER)
            return "cancelled"

        STATE.set_phase("P4")
        STATE.log_msg("P4: artifacts…")
        return _finish_artifacts(
            item=item,
            run_dir=run_dir,
            enriched=enriched,
            summary=summary,
            limit=limit,
            started_at=started_at,
            platform_id=PLATFORM_ROSTENDER,
        )
    except AuthError as e:
        STATE.set_session("expired")
        _ingest_step(
            item=item,
            status="error",
            rows=enriched,
            started_at=started_at,
            error=f"AuthError: {e}",
        )
        STATE.log_msg(f"AuthError: {e}", level="error")
        return "error"
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


def _run_tender_pro(*, item: dict, run_dir: Path) -> str:
    base = os.getenv("TENDER_PRO_BASE_URL", tender_pro_worker.DEFAULT_BASE)
    tp_cookies = _cookies_path(PLATFORM_TENDER_PRO)
    tp_probe = tender_pro_worker.probe_tender_pro_cookies(
        tp_cookies, base, on_retry=_http_retry_callback
    )
    if tp_probe == "missing":
        STATE.set_session("missing_cookies", platform_id=PLATFORM_TENDER_PRO)
        STATE.log_msg("Tender.Pro cookies missing — skip step", level="warn")
        _ingest_step(
            item=item,
            status="skipped",
            rows=[],
            started_at=datetime.now(timezone.utc),
        )
        return "skipped"
    if tp_probe == "expired":
        STATE.set_session("expired", platform_id=PLATFORM_TENDER_PRO)
        STATE.log_msg("Tender.Pro session expired — skip step", level="warn")
        _ingest_step(
            item=item,
            status="skipped",
            rows=[],
            started_at=datetime.now(timezone.utc),
        )
        return "skipped"
    queries = [str(q) for q in (item.get("queries") or []) if str(q).strip()]
    exclude = [str(x) for x in (item.get("exclude") or []) if str(x).strip()]
    limit = int(item.get("limit_n") or 0)
    started_at = datetime.now(timezone.utc)
    enriched: list[dict] = []
    summary: dict = {}
    try:
        STATE.set_phase("P1")
        STATE.log_msg("P1: Tender.Pro list scrape…")
        rows = tender_pro_worker.scrape_queries(
            queries=queries,
            limit=limit,
            base_url=base,
            exclude=exclude,
            should_stop=STATE.should_stop,
            on_retry=_http_retry_callback,
            on_progress=lambda n, lim: STATE.set_list_progress(n, lim),
        )
        rows = prefix_rows(rows, PLATFORM_TENDER_PRO)
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
            _ingest_step(
                item=item,
                status="stopped",
                rows=_board_rows(scored),
                started_at=started_at,
            )
            return "cancelled"

        STATE.set_phase("P3")
        STATE.log_msg("P3: Tender.Pro public cards…")
        enriched, errors = tender_pro_worker.enrich_cards(
            scored,
            card_ids,
            base_url=base,
            delay_s=0.2,
            should_stop=STATE.should_stop,
            on_retry=_http_retry_callback,
            on_progress=lambda d, t: STATE.set_cards_progress(d, t),
        )
        old_summary = dict(summary)
        enriched, summary, card_ids = rescore_rows(enriched)
        _apply_rescore_counter_delta(old_summary, summary)
        _write_scored_bundle(run_dir, enriched, summary, card_ids)
        (run_dir / "cards-errors.json").write_text(
            json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        STATE.log_msg(f"P3 done: errors={len(errors)}; re-score tiers={summary}")
        if STATE.should_stop():
            STATE.set_phase("P4")
            write_artifacts(run_dir, enriched)
            STATE.log_msg("Stopped during/after P3; partial artifacts written", level="warn")
            _ingest_step(
                item=item,
                status="stopped",
                rows=_board_rows(enriched),
                started_at=started_at,
            )
            _download_docs(enriched, platform_id=PLATFORM_TENDER_PRO)
            return "cancelled"

        STATE.set_phase("P4")
        STATE.log_msg("P4: artifacts…")
        return _finish_artifacts(
            item=item,
            run_dir=run_dir,
            enriched=enriched,
            summary=summary,
            limit=limit,
            started_at=started_at,
            platform_id=PLATFORM_TENDER_PRO,
        )
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


def _run_roseltorg(*, item: dict, run_dir: Path) -> str:
    cookies = _cookies_path(PLATFORM_ROSELTORG)
    base = os.getenv("ROSELTORG_BASE_URL", roseltorg_worker.DEFAULT_BASE)
    if not roseltorg_worker.cookies_present():
        STATE.set_session("missing_cookies", platform_id=PLATFORM_ROSELTORG)
        STATE.log_msg("Росэлторг: нет cookies.roseltorg.txt — skip", level="warn")
        _ingest_step(
            item=item,
            status="skipped",
            rows=[],
            started_at=datetime.now(timezone.utc),
        )
        return "skipped"
    probe = roseltorg_worker.probe_roseltorg_session(
        cookies_file=cookies, base=base, on_retry=_http_retry_callback
    )
    if probe == "missing":
        STATE.set_session("missing_cookies", platform_id=PLATFORM_ROSELTORG)
        STATE.log_msg("Росэлторг: cookies пустые — skip", level="warn")
        _ingest_step(
            item=item,
            status="skipped",
            rows=[],
            started_at=datetime.now(timezone.utc),
        )
        return "skipped"
    if probe == "expired":
        STATE.set_session("expired", platform_id=PLATFORM_ROSELTORG)
        STATE.log_msg("Росэлторг: сессия www недоступна — skip", level="warn")
        _ingest_step(
            item=item,
            status="skipped",
            rows=[],
            started_at=datetime.now(timezone.utc),
        )
        return "skipped"
    STATE.set_session("ok", platform_id=PLATFORM_ROSELTORG)
    queries = [str(q) for q in (item.get("queries") or []) if str(q).strip()]
    exclude = [str(x) for x in (item.get("exclude") or []) if str(x).strip()]
    limit = int(item.get("limit_n") or 0)
    started_at = datetime.now(timezone.utc)
    enriched: list[dict] = []
    scored: list[dict] = []
    summary: dict = {}
    try:
        STATE.set_phase("P1")
        STATE.log_msg("P1: Росэлторг www list…")
        rows = roseltorg_worker.scrape_queries(
            queries=queries,
            limit=limit,
            base=base,
            cookies_file=cookies,
            exclude=exclude,
            should_stop=STATE.should_stop,
            on_retry=_http_retry_callback,
            on_progress=lambda n, lim: STATE.set_list_progress(n, lim),
        )
        rows = prefix_rows(rows, PLATFORM_ROSELTORG)
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
            _ingest_step(
                item=item,
                status="stopped",
                rows=_board_rows(scored),
                started_at=started_at,
            )
            return "cancelled"

        STATE.set_phase("P3")
        STATE.log_msg("P3: Росэлторг procedure cards…")
        enriched, errors = roseltorg_worker.enrich_cards(
            scored,
            card_ids,
            cookies_file=cookies,
            base=base,
            delay_s=0.2,
            should_stop=STATE.should_stop,
            on_retry=_http_retry_callback,
            on_progress=lambda d, t: STATE.set_cards_progress(d, t),
        )
        old_summary = dict(summary)
        enriched, summary, card_ids = rescore_rows(enriched)
        _apply_rescore_counter_delta(old_summary, summary)
        _write_scored_bundle(run_dir, enriched, summary, card_ids)
        (run_dir / "cards-errors.json").write_text(
            json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        STATE.log_msg(f"P3 done: errors={len(errors)}; re-score tiers={summary}")
        if STATE.should_stop():
            STATE.set_phase("P4")
            write_artifacts(run_dir, enriched)
            STATE.log_msg("Stopped during/after P3; partial artifacts written", level="warn")
            _ingest_step(
                item=item,
                status="stopped",
                rows=_board_rows(enriched),
                started_at=started_at,
            )
            _download_docs(enriched, platform_id=PLATFORM_ROSELTORG)
            return "cancelled"

        STATE.set_phase("P4")
        STATE.log_msg("P4: artifacts…")
        return _finish_artifacts(
            item=item,
            run_dir=run_dir,
            enriched=enriched,
            summary=summary,
            limit=limit,
            started_at=started_at,
            platform_id=PLATFORM_ROSELTORG,
        )
    except AuthError as e:
        STATE.set_session("expired", platform_id=PLATFORM_ROSELTORG)
        _ingest_step(
            item=item,
            status="error",
            rows=_board_rows(enriched or scored),
            started_at=started_at,
            error=f"AuthError: {e}",
        )
        STATE.log_msg(f"AuthError: {e}", level="error")
        return "error"
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

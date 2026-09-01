"""Background P1–P4 runner for operator UI — queue of named searches (023/024)."""
from __future__ import annotations

import json
import os
import threading
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

from app.api import search_groups as search_groups_api
from app.api.notify import notify_ops_session
from app.api.state import STATE
from app.scoring.pipeline import rescore_rows, score_rows
from app.worker import b2b_center as b2b_center_worker
from app.worker import oilb2bcs as oilb2bcs_worker
from app.worker import roseltorg as roseltorg_worker
from app.worker import rts_rosatom as rts_rosatom_worker
from app.worker import tender_pro as tender_pro_worker
from app.worker.artifacts import write_artifacts
from app.worker.card_scrape import enrich_cards
from app.worker.docs import download_docs_enabled, download_inbox_docs
from app.deadline import drop_past_deadline_rows
from app.worker.ingest import ingest_run, redact_db_error, snapshot_expired_tender_ids
from app.worker.list_scrape import AuthError, probe_rostender_cookies, scrape_queries
from app.worker.platform_ids import (
    PLATFORM_B2B_CENTER,
    PLATFORM_OILB2BCS,
    PLATFORM_ROSELTORG,
    PLATFORM_ROSTENDER,
    PLATFORM_RTS_ROSATOM,
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
    elif platform_id == PLATFORM_B2B_CENTER:
        raw = os.getenv("B2B_CENTER_COOKIES_FILE", "./cookies.b2b-center.txt")
    elif platform_id == PLATFORM_RTS_ROSATOM:
        raw = os.getenv("RTS_ROSATOM_COOKIES_FILE", "./cookies.rts-rosatom.txt")
    elif platform_id == PLATFORM_OILB2BCS:
        raw = os.getenv("OILB2BCS_COOKIES_FILE", "./cookies.oilb2bcs.txt")
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
    else:
        # File present; skip live probe on poll — do not invent ok over a
        # fresh upload/run probe (expired/missing must stick until live check).
        current = str((STATE.snapshot().get("sessions") or {}).get(PLATFORM_ROSELTORG) or "")
        if current in {"unknown", "", "missing", "missing_cookies"}:
            STATE.set_session("ok", platform_id=PLATFORM_ROSELTORG)

    b2b_cookies = _cookies_path(PLATFORM_B2B_CENTER)
    b2b_base = os.getenv("B2B_CENTER_BASE_URL", b2b_center_worker.DEFAULT_BASE)
    b2b_probe = b2b_center_worker.probe_b2b_center_session(
        b2b_cookies, b2b_base, on_retry=_http_retry_callback
    )
    if b2b_probe == "missing":
        STATE.set_session("missing_cookies", platform_id=PLATFORM_B2B_CENTER)
    elif b2b_probe == "expired":
        STATE.set_session("expired", platform_id=PLATFORM_B2B_CENTER)
    elif b2b_probe == "blocked":
        STATE.set_session("blocked", platform_id=PLATFORM_B2B_CENTER)
    else:
        STATE.set_session("ok", platform_id=PLATFORM_B2B_CENTER)

    rts_cookies = _cookies_path(PLATFORM_RTS_ROSATOM)
    rts_base = os.getenv("RTS_ROSATOM_BASE_URL", rts_rosatom_worker.DEFAULT_BASE)
    rts_probe = rts_rosatom_worker.probe_rts_rosatom_session(
        rts_cookies, rts_base, on_retry=_http_retry_callback
    )
    if rts_probe == "missing":
        STATE.set_session("missing_cookies", platform_id=PLATFORM_RTS_ROSATOM)
    elif rts_probe == "expired":
        STATE.set_session("expired", platform_id=PLATFORM_RTS_ROSATOM)
    elif rts_probe == "blocked":
        STATE.set_session("blocked", platform_id=PLATFORM_RTS_ROSATOM)
    else:
        STATE.set_session("ok", platform_id=PLATFORM_RTS_ROSATOM)

    oil_cookies = _cookies_path(PLATFORM_OILB2BCS)
    oil_base = os.getenv("OILB2BCS_BASE_URL", oilb2bcs_worker.DEFAULT_BASE)
    oil_probe = oilb2bcs_worker.probe_oilb2bcs_session(
        oil_cookies, oil_base, on_retry=_http_retry_callback
    )
    if oil_probe == "missing":
        STATE.set_session("missing_cookies", platform_id=PLATFORM_OILB2BCS)
    elif oil_probe == "expired":
        STATE.set_session("expired", platform_id=PLATFORM_OILB2BCS)
    else:
        STATE.set_session("ok", platform_id=PLATFORM_OILB2BCS)
    return STATE.snapshot()["session"]


def start_run(*, pipeline: str = "manual", from_ticker: bool = False) -> bool:
    global _thread
    if pipeline not in {"manual", "auto"}:
        raise RuntimeError("invalid_pipeline")
    with _lock:
        if STATE.snapshot()["running"]:
            if from_ticker:
                from app.api.schedule import SKIP_ALREADY_RUNNING, record_slot_skip

                record_slot_skip(SKIP_ALREADY_RUNNING)
                return False
            raise RuntimeError("already_running")
        try:
            items = search_groups_api.get_queued_steps()
        except RuntimeError as exc:
            if str(exc) == "database_unconfigured":
                if from_ticker:
                    from app.api.schedule import SKIP_EMPTY_QUEUE, record_slot_skip

                    record_slot_skip(SKIP_EMPTY_QUEUE)
                    return False
                raise RuntimeError("empty_queue") from exc
            raise
        if not items:
            if from_ticker:
                from app.api.schedule import SKIP_EMPTY_QUEUE, record_slot_skip

                record_slot_skip(SKIP_EMPTY_QUEUE)
                return False
            raise RuntimeError("empty_queue")
        refresh_session()
        run_dir = _repo_root() / "runs" / date.today().isoformat()
        run_dir.mkdir(parents=True, exist_ok=True)
        try:
            STATE.reset_for_queue(items=items, run_dir=str(run_dir), pipeline=pipeline)
            STATE.log_msg(f"Queue: {len(items)} step(s) ({pipeline})")
            _thread = threading.Thread(
                target=_run_queue,
                kwargs={"items": items, "run_dir": run_dir, "pipeline": pipeline},
                daemon=True,
            )
            _thread.start()
        except Exception:
            STATE.finish("error", error="start_failed")
            raise
        if pipeline == "auto":
            from app.api.schedule import record_slot_fire

            try:
                record_slot_fire()
            except Exception as exc:  # noqa: BLE001 — queue already running
                STATE.log_msg(f"Schedule fire mark: {type(exc).__name__}", level="warn")
        return True


def request_stop() -> None:
    STATE.request_stop()
    STATE.log_msg("Stop requested (soft)", level="warn")


def _query_label(item: dict) -> str:
    name = str(item.get("group_name") or item.get("name") or "")
    platform = str(item.get("platform_id") or "")
    if platform:
        name = f"{name} × {platform}" if name else platform
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
    rows, dropped_past = drop_past_deadline_rows(rows)
    if dropped_past:
        STATE.log_msg(
            f"Отсев просроченного срока перед ingest: {dropped_past}",
            level="warn",
        )
    search_group_id: UUID | None = None
    raw_id = item.get("group_id") or item.get("id")
    if raw_id:
        try:
            search_group_id = UUID(str(raw_id))
        except ValueError:
            search_group_id = None
    try:
        result = ingest_run(
            query=_query_label(item),
            limit_n=int(item.get("limit_n") or 0),
            status=status,
            rows=rows,
            started_at=started_at,
            source_platform_id=str(item.get("platform_id") or PLATFORM_ROSTENDER),
            search_group_id=search_group_id,
            pipeline=STATE.current_pipeline(),
        )
        if result is None:
            STATE.log_msg("Ingest skipped (database unconfigured)", level="warn")
        else:
            STATE.add_run_report(
                new=result.new_count,
                already=result.already_count,
                updated=result.updated_count,
            )
            STATE.add_affected_ids(list(result.new_ids) + list(result.updated_ids))
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
    if platform_id == PLATFORM_TENDER_PRO:
        if not cookies.is_file():
            STATE.log_msg("Docs: Tender.Pro cookies missing — skip files", level="warn")
            return
        tp_base = os.getenv("TENDER_PRO_BASE_URL", tender_pro_worker.DEFAULT_BASE)
        tp_probe = tender_pro_worker.probe_tender_pro_cookies(
            cookies, tp_base, on_retry=_http_retry_callback
        )
        if tp_probe != "ok":
            STATE.log_msg(
                f"Docs: Tender.Pro session {tp_probe} — skip files",
                level="warn",
            )
            return
    if platform_id == PLATFORM_B2B_CENTER:
        if not cookies.is_file():
            STATE.log_msg("Docs: B2B-Center cookies missing — skip files", level="warn")
            return
        b2b_base = os.getenv("B2B_CENTER_BASE_URL", b2b_center_worker.DEFAULT_BASE)
        b2b_probe = b2b_center_worker.probe_b2b_center_session(
            cookies, b2b_base, on_retry=_http_retry_callback
        )
        if b2b_probe != "ok":
            STATE.log_msg(
                f"Docs: B2B-Center session {b2b_probe} — skip files",
                level="warn",
            )
            return
    if platform_id == PLATFORM_RTS_ROSATOM:
        if not cookies.is_file():
            STATE.log_msg("Docs: РТС Росатом cookies missing — skip files", level="warn")
            return
        rts_base = os.getenv("RTS_ROSATOM_BASE_URL", rts_rosatom_worker.DEFAULT_BASE)
        rts_probe = rts_rosatom_worker.probe_rts_rosatom_session(
            cookies, rts_base, on_retry=_http_retry_callback
        )
        if rts_probe != "ok":
            STATE.log_msg(
                f"Docs: РТС Росатом session {rts_probe} — skip files",
                level="warn",
            )
            return
    if platform_id == PLATFORM_OILB2BCS:
        STATE.log_msg("Docs: OilB2B — скачивание файлов не поддержано", level="warn")
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
            STATE.set_session("expired", platform_id=platform_id)
        STATE.log_msg(f"Docs AuthError: {exc}", level="error")
    except Exception as exc:  # noqa: BLE001
        STATE.log_msg(f"Docs error: {type(exc).__name__}: {exc}", level="error")


def _run_queue(*, items: list[dict], run_dir: Path, pipeline: str = "manual") -> None:
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
    if pipeline == "auto" and overall in {"done", "partial"}:
        prefer = STATE.affected_ids()
        try:
            from app.api.inbox import run_auto_ai_review

            run_auto_ai_review(prefer)
        except Exception as exc:  # noqa: BLE001
            STATE.log_msg(f"Auto AI: {type(exc).__name__}: {exc}", level="error")
    STATE.finish(overall)


def _run_one_search(*, item: dict, run_dir: Path) -> str:
    platform = str(item.get("platform_id") or "")
    if platform == PLATFORM_TENDER_PRO:
        return _run_tender_pro(item=item, run_dir=run_dir)
    if platform == PLATFORM_ROSELTORG:
        return _run_roseltorg(item=item, run_dir=run_dir)
    if platform == PLATFORM_B2B_CENTER:
        return _run_b2b_center(item=item, run_dir=run_dir)
    if platform == PLATFORM_RTS_ROSATOM:
        return _run_rts_rosatom(item=item, run_dir=run_dir)
    if platform == PLATFORM_OILB2BCS:
        return _run_oilb2bcs(item=item, run_dir=run_dir)
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
        notify_ops_session(platform_id=PLATFORM_ROSTENDER, session=probe)
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
    # List + public cards run without jar; docs skip when probe != ok (055).
    if tp_probe == "missing":
        STATE.set_session("missing_cookies", platform_id=PLATFORM_TENDER_PRO)
        STATE.log_msg("Tender.Pro cookies missing — list without login", level="warn")
    elif tp_probe == "expired":
        STATE.set_session("expired", platform_id=PLATFORM_TENDER_PRO)
        STATE.log_msg("Tender.Pro session expired — list without login", level="warn")
    else:
        STATE.set_session("ok", platform_id=PLATFORM_TENDER_PRO)
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


def _run_b2b_center(*, item: dict, run_dir: Path) -> str:
    base = os.getenv("B2B_CENTER_BASE_URL", b2b_center_worker.DEFAULT_BASE)
    b2b_cookies = _cookies_path(PLATFORM_B2B_CENTER)
    b2b_probe = b2b_center_worker.probe_b2b_center_session(
        b2b_cookies, base, on_retry=_http_retry_callback
    )
    # List + view.html cards run without jar; docs skip when probe != ok.
    if b2b_probe == "missing":
        STATE.set_session("missing_cookies", platform_id=PLATFORM_B2B_CENTER)
        STATE.log_msg("B2B-Center cookies missing — list without login", level="warn")
    elif b2b_probe == "expired":
        STATE.set_session("expired", platform_id=PLATFORM_B2B_CENTER)
        STATE.log_msg("B2B-Center session expired — list without login", level="warn")
    elif b2b_probe == "blocked":
        STATE.set_session("blocked", platform_id=PLATFORM_B2B_CENTER)
        STATE.log_msg("B2B-Center captcha — list without login", level="warn")
    else:
        STATE.set_session("ok", platform_id=PLATFORM_B2B_CENTER)
    queries = [str(q) for q in (item.get("queries") or []) if str(q).strip()]
    exclude = [str(x) for x in (item.get("exclude") or []) if str(x).strip()]
    limit = int(item.get("limit_n") or 0)
    started_at = datetime.now(timezone.utc)
    enriched: list[dict] = []
    summary: dict = {}
    try:
        STATE.set_phase("P1")
        STATE.log_msg("P1: B2B-Center list scrape…")
        rows = b2b_center_worker.scrape_queries(
            queries=queries,
            limit=limit,
            base=base,
            cookies_file=b2b_cookies if b2b_cookies.is_file() else None,
            exclude=exclude,
            should_stop=STATE.should_stop,
            on_retry=_http_retry_callback,
            on_progress=lambda n, lim: STATE.set_list_progress(n, lim),
        )
        rows = prefix_rows(rows, PLATFORM_B2B_CENTER)
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
        STATE.log_msg("P3: B2B-Center view.html cards…")
        enriched, errors = b2b_center_worker.enrich_cards(
            scored,
            card_ids,
            base=base,
            cookies_file=b2b_cookies if b2b_cookies.is_file() else None,
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
            _download_docs(enriched, platform_id=PLATFORM_B2B_CENTER)
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
            platform_id=PLATFORM_B2B_CENTER,
        )
    except AuthError as e:
        STATE.set_session("expired", platform_id=PLATFORM_B2B_CENTER)
        notify_ops_session(platform_id=PLATFORM_B2B_CENTER, session="expired")
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


def _run_cookie_platform(
    *,
    item: dict,
    run_dir: Path,
    platform_id: str,
    probe_session,
    scrape_queries_fn,
    enrich_cards_fn,
    base_env: str,
    default_base: str,
    label: str,
    require_ok_session: bool,
    p1_log: str,
    p3_log: str,
) -> str:
    base = os.getenv(base_env, default_base)
    cookies = _cookies_path(platform_id)
    probe = probe_session(cookies, base, on_retry=_http_retry_callback)
    if probe == "missing":
        STATE.set_session("missing_cookies", platform_id=platform_id)
        STATE.log_msg(f"{label}: нет cookies", level="error" if require_ok_session else "warn")
        if require_ok_session:
            notify_ops_session(platform_id=platform_id, session="missing")
            _ingest_step(
                item=item,
                status="error",
                rows=[],
                started_at=datetime.now(timezone.utc),
                error="missing_cookies",
            )
            return "error"
    elif probe == "expired":
        STATE.set_session("expired", platform_id=platform_id)
        STATE.log_msg(f"{label}: сессия устарела", level="error" if require_ok_session else "warn")
        if require_ok_session:
            notify_ops_session(platform_id=platform_id, session="expired")
            _ingest_step(
                item=item,
                status="error",
                rows=[],
                started_at=datetime.now(timezone.utc),
                error="session_expired",
            )
            return "error"
    elif probe == "blocked":
        STATE.set_session("blocked", platform_id=platform_id)
        STATE.log_msg(f"{label}: captcha — прогон невозможен", level="error")
        notify_ops_session(platform_id=platform_id, session="blocked")
        _ingest_step(
            item=item,
            status="error",
            rows=[],
            started_at=datetime.now(timezone.utc),
            error="captcha_blocked",
        )
        return "error"
    else:
        STATE.set_session("ok", platform_id=platform_id)

    queries = [str(q) for q in (item.get("queries") or []) if str(q).strip()]
    exclude = [str(x) for x in (item.get("exclude") or []) if str(x).strip()]
    limit = int(item.get("limit_n") or 0)
    started_at = datetime.now(timezone.utc)
    enriched: list[dict] = []
    summary: dict = {}
    cookies_arg = cookies if cookies.is_file() else None
    try:
        STATE.set_phase("P1")
        STATE.log_msg(p1_log)
        rows = scrape_queries_fn(
            queries=queries,
            limit=limit,
            base=base,
            cookies_file=cookies_arg,
            exclude=exclude,
            should_stop=STATE.should_stop,
            on_retry=_http_retry_callback,
            on_progress=lambda n, lim: STATE.set_list_progress(n, lim),
        )
        rows = prefix_rows(rows, platform_id)
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
        STATE.log_msg(p3_log)
        enriched, errors = enrich_cards_fn(
            scored,
            card_ids,
            base=base,
            cookies_file=cookies_arg,
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
            _download_docs(enriched, platform_id=platform_id)
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
            platform_id=platform_id,
        )
    except AuthError as e:
        session = "blocked" if "captcha" in str(e) else "expired"
        STATE.set_session(session, platform_id=platform_id)
        notify_ops_session(platform_id=platform_id, session=session)
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


def _run_rts_rosatom(*, item: dict, run_dir: Path) -> str:
    return _run_cookie_platform(
        item=item,
        run_dir=run_dir,
        platform_id=PLATFORM_RTS_ROSATOM,
        probe_session=rts_rosatom_worker.probe_rts_rosatom_session,
        scrape_queries_fn=rts_rosatom_worker.scrape_queries,
        enrich_cards_fn=rts_rosatom_worker.enrich_cards,
        base_env="RTS_ROSATOM_BASE_URL",
        default_base=rts_rosatom_worker.DEFAULT_BASE,
        label="РТС Росатом",
        require_ok_session=True,
        p1_log="P1: РТС Росатом list scrape…",
        p3_log="P3: РТС Росатом view.html cards…",
    )


def _run_oilb2bcs(*, item: dict, run_dir: Path) -> str:
    return _run_cookie_platform(
        item=item,
        run_dir=run_dir,
        platform_id=PLATFORM_OILB2BCS,
        probe_session=oilb2bcs_worker.probe_oilb2bcs_session,
        scrape_queries_fn=oilb2bcs_worker.scrape_queries,
        enrich_cards_fn=oilb2bcs_worker.enrich_cards,
        base_env="OILB2BCS_BASE_URL",
        default_base=oilb2bcs_worker.DEFAULT_BASE,
        label="OilB2B",
        require_ok_session=True,
        p1_log="P1: OilB2B GetClaims list…",
        p3_log="P3: OilB2B card markers…",
    )


def _run_roseltorg(*, item: dict, run_dir: Path) -> str:
    cookies = _cookies_path(PLATFORM_ROSELTORG)
    base = os.getenv("ROSELTORG_BASE_URL", roseltorg_worker.DEFAULT_BASE)

    if not roseltorg_worker.cookies_present():
        STATE.set_session("missing_cookies", platform_id=PLATFORM_ROSELTORG)
        STATE.log_msg("Росэлторг: нет cookies.roseltorg.txt — skip", level="warn")
        notify_ops_session(platform_id=PLATFORM_ROSELTORG, session="missing")
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
        notify_ops_session(platform_id=PLATFORM_ROSELTORG, session="missing")
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
        notify_ops_session(platform_id=PLATFORM_ROSELTORG, session="expired")
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

"""CLI: P1 list scrape + P2 scoring + P3 cards + P4 artifacts + P5.3 ingest."""
from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from app.scoring.pipeline import score_rows
from app.worker.artifacts import write_artifacts
from app.worker.card_scrape import enrich_cards
from app.worker.docs import download_docs_enabled, download_inbox_docs
from app.worker.ingest import ingest_run, redact_db_error
from app.worker.list_scrape import AuthError, scrape_list


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_out() -> Path:
    return _repo_root() / "runs" / date.today().isoformat()


def _cookies_path(args: argparse.Namespace) -> Path:
    load_dotenv(_repo_root() / ".env")
    cookies = Path(
        getattr(args, "cookies", None) or os.getenv("ROSTENDER_COOKIES_FILE", "./cookies.rostender.txt")
    )
    if not cookies.is_absolute():
        cookies = _repo_root() / cookies
    return cookies


def _append_readme(out_dir: Path, section: str) -> None:
    readme = out_dir / "README.md"
    prev = readme.read_text(encoding="utf-8") if readme.is_file() else f"# Run {out_dir.name}\n\n"
    readme.write_text(prev + "\n" + section, encoding="utf-8")


def cmd_scrape(args: argparse.Namespace) -> int:
    cookies = _cookies_path(args)
    base = args.base or os.getenv("ROSTENDER_BASE_URL", "https://rostender.info")
    out_dir = Path(args.out) if args.out else _default_out()
    out_dir.mkdir(parents=True, exist_ok=True)

    readme = out_dir / "README.md"
    try:
        rows = scrape_list(
            cookies_path=cookies,
            base_url=base,
            query=args.query,
            limit=args.limit,
            headless=not args.headed,
        )
    except AuthError as e:
        readme.write_text(
            f"# Run {out_dir.name}\n\n**status:** blocked\n\n**phase:** P1\n\n**error:** AuthError — {e}\n",
            encoding="utf-8",
        )
        print(f"AUTH ERROR: {e}")
        return 2
    except Exception as e:  # noqa: BLE001
        readme.write_text(
            f"# Run {out_dir.name}\n\n**status:** error\n\n**phase:** P1\n\n**error:** {type(e).__name__}: {e}\n",
            encoding="utf-8",
        )
        print(f"ERROR: {e}")
        return 1

    raw_path = out_dir / "raw-list.json"
    raw_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    readme.write_text(
        f"# Run {out_dir.name}\n\n"
        f"**status:** ok\n\n"
        f"**phase:** P1\n\n"
        f"**query:** {args.query}\n\n"
        f"**count:** {len(rows)}\n\n"
        f"**files:** `raw-list.json`\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(rows)} rows → {raw_path}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    out_dir = Path(args.out) if args.out else _default_out()
    raw_path = Path(args.raw) if args.raw else out_dir / "raw-list.json"
    if not raw_path.is_file():
        print(f"raw-list not found: {raw_path}")
        return 1
    rows = json.loads(raw_path.read_text(encoding="utf-8"))
    scored, summary, card_ids = score_rows(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "scored-list.json").write_text(
        json.dumps(scored, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "tier-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "card-ids.json").write_text(
        json.dumps(card_ids, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _append_readme(
        out_dir,
        f"## P2 scoring\n\n**tiers:** {summary}\n\n"
        f"**card candidates (L1∪L2∪L3):** {len(card_ids)}\n\n"
        f"**files:** `scored-list.json`, `tier-summary.json`, `card-ids.json`\n",
    )
    print(f"Scored {len(scored)} → {out_dir / 'scored-list.json'}")
    print(f"Summary: {summary}")
    return 0


def cmd_cards(args: argparse.Namespace) -> int:
    out_dir = Path(args.out) if args.out else _default_out()
    scored_path = out_dir / "scored-list.json"
    ids_path = out_dir / "card-ids.json"
    if not scored_path.is_file():
        print(f"missing {scored_path}")
        return 1
    rows = json.loads(scored_path.read_text(encoding="utf-8"))
    if ids_path.is_file():
        card_ids = json.loads(ids_path.read_text(encoding="utf-8"))
    else:
        card_ids = [r["tender_id"] for r in rows if r.get("tier") in ("L1", "L2", "L3")]
    cookies = _cookies_path(args)
    try:
        enriched, errors = enrich_cards(
            rows, card_ids, cookies_path=cookies, delay_s=args.delay
        )
    except AuthError as e:
        _append_readme(out_dir, f"## P3 cards\n\n**status:** blocked\n\n**error:** {e}\n")
        print(f"AUTH ERROR: {e}")
        return 2

    scored_path.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "cards-errors.json").write_text(
        json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ok = sum(1 for r in enriched if r.get("card_fetched"))
    _append_readme(
        out_dir,
        f"## P3 cards\n\n**fetched ok:** {ok}/{len(card_ids)}\n\n"
        f"**errors:** {len(errors)}\n\n"
        f"**files:** `scored-list.json` (enriched), `cards-errors.json`\n",
    )
    print(f"Cards ok={ok} errors={len(errors)}")
    return 0


def cmd_artifacts(args: argparse.Namespace) -> int:
    out_dir = Path(args.out) if args.out else _default_out()
    scored_path = out_dir / "scored-list.json"
    if not scored_path.is_file():
        print(f"missing {scored_path}")
        return 1
    rows = json.loads(scored_path.read_text(encoding="utf-8"))
    summary = write_artifacts(out_dir, rows)
    _append_readme(
        out_dir,
        f"## P4 artifacts\n\n**tiers:** {summary}\n\n"
        f"**files:** `tenders.csv`, `tenders.md`, `priority-fit.md`\n",
    )
    print(f"Artifacts → {out_dir}")
    query = getattr(args, "query", None) or "неразрушающий"
    limit_n = getattr(args, "limit", None) or 1000
    try:
        result = ingest_run(query=query, limit_n=int(limit_n), status="done", rows=rows)
    except Exception as exc:  # noqa: BLE001
        print(f"INGEST ERROR: {redact_db_error(exc)}")
        return 1
    if result is None:
        print("Ingest skipped (database unconfigured)")
    else:
        print(f"Ingest: {result.lot_count} lots (score≥4)")
    if download_docs_enabled():
        try:
            docs = download_inbox_docs(rows, cookies_path=_cookies_path(args), delay_s=0.2)
        except AuthError as exc:
            print(f"DOCS AUTH ERROR: {exc}")
            return 2
        except Exception as exc:  # noqa: BLE001
            print(f"DOCS ERROR: {redact_db_error(exc)}")
            return 1
        print(f"Docs: saved={docs.saved} skipped={docs.skipped} errors={docs.errors}")
    else:
        print("Docs: skip (DOWNLOAD_DOCS=0)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ndt-tender-scout")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("scrape", help="P1: scrape list up to N rows")
    p1.add_argument("--cookies", default=None)
    p1.add_argument("--base", default=None)
    p1.add_argument("--query", default="неразрушающий")
    p1.add_argument("--limit", type=int, default=1000)
    p1.add_argument("--out", default=None)
    p1.add_argument("--headed", action="store_true")
    p1.set_defaults(func=cmd_scrape)

    p2 = sub.add_parser("score", help="P2: score raw-list.json")
    p2.add_argument("--raw", default=None)
    p2.add_argument("--out", default=None)
    p2.set_defaults(func=cmd_score)

    p3 = sub.add_parser("cards", help="P3: fetch cards for L1–L3")
    p3.add_argument("--cookies", default=None)
    p3.add_argument("--out", default=None)
    p3.add_argument("--delay", type=float, default=0.25)
    p3.set_defaults(func=cmd_cards)

    p4 = sub.add_parser("artifacts", help="P4: CSV/MD/priority-fit")
    p4.add_argument("--out", default=None)
    p4.add_argument("--cookies", default=None)
    p4.set_defaults(func=cmd_artifacts)

    both = sub.add_parser("run", help="P1→P2→P3→P4 (or --from-score skips P1)")
    both.add_argument("--cookies", default=None)
    both.add_argument("--base", default=None)
    both.add_argument("--query", default="неразрушающий")
    both.add_argument("--limit", type=int, default=1000)
    both.add_argument("--out", default=None)
    both.add_argument("--headed", action="store_true")
    both.add_argument("--delay", type=float, default=0.25)
    both.add_argument(
        "--from-score",
        action="store_true",
        help="Skip P1/P2; run cards+artifacts on existing scored-list",
    )

    def cmd_run(a: argparse.Namespace) -> int:
        if not a.from_score:
            rc = cmd_scrape(a)
            if rc != 0:
                return rc
            a.raw = None
            rc = cmd_score(a)
            if rc != 0:
                return rc
        rc = cmd_cards(a)
        if rc != 0:
            return rc
        return cmd_artifacts(a)

    both.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

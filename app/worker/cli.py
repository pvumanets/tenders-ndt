"""CLI: P1 list scrape + P2 scoring."""
from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from app.scoring.pipeline import score_rows
from app.worker.list_scrape import AuthError, scrape_list


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_out() -> Path:
    return _repo_root() / "runs" / date.today().isoformat()


def cmd_scrape(args: argparse.Namespace) -> int:
    load_dotenv(_repo_root() / ".env")
    cookies = Path(args.cookies or os.getenv("ROSTENDER_COOKIES_FILE", "./cookies.rostender.txt"))
    if not cookies.is_absolute():
        cookies = _repo_root() / cookies
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
    scored_path = out_dir / "scored-list.json"
    summary_path = out_dir / "tier-summary.json"
    cards_path = out_dir / "card-ids.json"
    scored_path.write_text(json.dumps(scored, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    cards_path.write_text(json.dumps(card_ids, ensure_ascii=False, indent=2), encoding="utf-8")

    readme = out_dir / "README.md"
    prev = readme.read_text(encoding="utf-8") if readme.is_file() else f"# Run {out_dir.name}\n\n"
    readme.write_text(
        prev
        + f"\n## P2 scoring\n\n"
        f"**tiers:** {summary}\n\n"
        f"**card candidates (L1∪L2∪L3):** {len(card_ids)}\n\n"
        f"**files:** `scored-list.json`, `tier-summary.json`, `card-ids.json`\n",
        encoding="utf-8",
    )
    print(f"Scored {len(scored)} → {scored_path}")
    print(f"Summary: {summary}")
    print(f"Card IDs: {len(card_ids)} → {cards_path}")
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

    both = sub.add_parser("run", help="P1 then P2")
    both.add_argument("--cookies", default=None)
    both.add_argument("--base", default=None)
    both.add_argument("--query", default="неразрушающий")
    both.add_argument("--limit", type=int, default=1000)
    both.add_argument("--out", default=None)
    both.add_argument("--headed", action="store_true")

    def cmd_run(a: argparse.Namespace) -> int:
        rc = cmd_scrape(a)
        if rc != 0:
            return rc
        a.raw = None
        return cmd_score(a)

    both.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

"""Load scored-list.json for operator Results UI."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.api.state import STATE

FIT_TIERS = frozenset({"L1", "L2", "L3"})
SLIM_KEYS = (
    "tender_id",
    "rank",
    "score",
    "tier",
    "title",
    "price_rub",
    "location",
    "deadline_msk",
    "url",
    "methods",
    "fit_reason",
    "customer_name",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _runs_root() -> Path:
    return _repo_root() / "runs"


def resolve_run_dir(run_dir: str | None = None) -> Path | None:
    if run_dir:
        p = Path(run_dir)
        if (p / "scored-list.json").is_file():
            return p
    snap = STATE.snapshot()
    if snap.get("run_dir"):
        p = Path(snap["run_dir"])
        if (p / "scored-list.json").is_file():
            return p
    root = _runs_root()
    if not root.is_dir():
        return None
    candidates = sorted(
        (d for d in root.iterdir() if d.is_dir() and (d / "scored-list.json").is_file()),
        key=lambda d: d.name,
        reverse=True,
    )
    return candidates[0] if candidates else None


def load_scored(run_dir: Path | None = None) -> tuple[Path | None, list[dict[str, Any]]]:
    rd = resolve_run_dir(str(run_dir) if run_dir else None)
    if rd is None:
        return None, []
    path = rd / "scored-list.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return rd, []
    return rd, data


def _matches_q(row: dict[str, Any], q: str) -> bool:
    if not q:
        return True
    q = q.casefold()
    blob = " ".join(
        str(row.get(k) or "")
        for k in ("title", "customer_name", "location", "fit_reason", "tender_id", "methods")
    ).casefold()
    return q in blob


def _slim(row: dict[str, Any]) -> dict[str, Any]:
    out = {k: row.get(k) for k in SLIM_KEYS}
    fr = out.get("fit_reason")
    if isinstance(fr, str) and len(fr) > 160:
        out["fit_reason"] = fr[:157] + "…"
    return out


def list_results(
    *,
    tier: str = "fit",
    q: str = "",
    run_dir: str | None = None,
) -> dict[str, Any]:
    rd, rows = load_scored(Path(run_dir) if run_dir else None)
    if rd is None:
        return {"run_dir": None, "total": 0, "tier": tier, "q": q, "items": []}

    tier_norm = (tier or "fit").strip()
    if tier_norm == "fit":
        filtered = [r for r in rows if r.get("tier") in FIT_TIERS]
    elif tier_norm == "all":
        filtered = list(rows)
    elif tier_norm in ("L1", "L2", "L3", "noise", "pool"):
        filtered = [r for r in rows if r.get("tier") == tier_norm]
    else:
        filtered = [r for r in rows if r.get("tier") in FIT_TIERS]

    if q:
        filtered = [r for r in filtered if _matches_q(r, q)]

    # keep score/rank order as in file (already sorted); stable secondary by tender_id
    items = [_slim(r) for r in filtered]
    return {
        "run_dir": str(rd),
        "total": len(items),
        "tier": tier_norm,
        "q": q,
        "items": items,
    }


def get_result(tender_id: str, *, run_dir: str | None = None) -> dict[str, Any] | None:
    rd, rows = load_scored(Path(run_dir) if run_dir else None)
    if rd is None:
        return None
    tid = str(tender_id)
    for r in rows:
        if str(r.get("tender_id") or "") == tid:
            return {"run_dir": str(rd), "item": r}
    return None

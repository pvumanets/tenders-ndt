"""P2 pipeline over raw list rows."""
from __future__ import annotations

from collections import Counter

from app.scoring.tiers import assign_tier


def score_rows(rows: list[dict]) -> tuple[list[dict], dict, list[str]]:
    scored: list[dict] = []
    for i, row in enumerate(rows, start=1):
        title = row.get("title") or ""
        tier, score, fit_reason, uzk = assign_tier(title)
        item = dict(row)
        item["rank"] = i
        item["score"] = score
        item["tier"] = tier
        item["fit_reason"] = fit_reason
        item["uzk_service"] = uzk
        scored.append(item)

    # Re-rank by score desc within output order for convenience
    scored_sorted = sorted(scored, key=lambda r: (-int(r["score"]), r.get("rank", 0)))
    for i, row in enumerate(scored_sorted, start=1):
        row["rank"] = i

    summary = dict(Counter(r["tier"] for r in scored_sorted))
    for k in ("L1", "L2", "L3", "noise", "pool"):
        summary.setdefault(k, 0)

    card_ids = [r["tender_id"] for r in scored_sorted if r["tier"] in ("L1", "L2", "L3")]
    return scored_sorted, summary, card_ids

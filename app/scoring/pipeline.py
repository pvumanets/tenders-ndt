"""P2 pipeline over raw list rows; P14 re-score after card enrich."""
from __future__ import annotations

from collections import Counter

from app.scoring.tiers import assign_tier
from app.worker.platform_ids import PLATFORM_TENDER_PRO

_BOARD_TIERS = frozenset({"L1", "L2", "L3"})
_RESCORE_SNIPPET = 2000


def rescore_text(row: dict) -> str:
    parts: list[str] = []
    title = str(row.get("title") or "").strip()
    if title:
        parts.append(title)
    # methods — display only; do not score (037: no HTML inject into tier)
    for key in ("description", "fit_extra"):
        val = row.get(key)
        if val:
            parts.append(str(val)[:_RESCORE_SNIPPET])
    return "\n".join(parts)


def _is_tender_pro_row(row: dict) -> bool:
    tid = str(row.get("tender_id") or "")
    return tid.startswith(f"{PLATFORM_TENDER_PRO}:")


def _should_rescore(row: dict) -> bool:
    if row.get("card_fetched"):
        return True
    return _is_tender_pro_row(row)


def rescore_rows(rows: list[dict]) -> tuple[list[dict], dict, list[str]]:
    """Re-assign tiers using title + card/goods text (P14)."""
    for row in rows:
        if not _should_rescore(row):
            continue
        tier, score, fit_reason, uzk = assign_tier(rescore_text(row))
        row["tier"] = tier
        row["score"] = score
        row["fit_reason"] = fit_reason
        row["uzk_service"] = uzk

    scored_sorted = sorted(rows, key=lambda r: (-int(r.get("score") or 0), r.get("rank", 0)))
    for i, row in enumerate(scored_sorted, start=1):
        row["rank"] = i

    summary = dict(Counter(r["tier"] for r in scored_sorted))
    for key in ("L1", "L2", "L3", "noise", "pool"):
        summary.setdefault(key, 0)

    card_ids = [r["tender_id"] for r in scored_sorted if r["tier"] in _BOARD_TIERS]
    return scored_sorted, summary, card_ids


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

    scored_sorted = sorted(scored, key=lambda r: (-int(r["score"]), r.get("rank", 0)))
    for i, row in enumerate(scored_sorted, start=1):
        row["rank"] = i

    summary = dict(Counter(r["tier"] for r in scored_sorted))
    for k in ("L1", "L2", "L3", "noise", "pool"):
        summary.setdefault(k, 0)

    card_ids = [r["tender_id"] for r in scored_sorted if r["tier"] in _BOARD_TIERS]
    return scored_sorted, summary, card_ids

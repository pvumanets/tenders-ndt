"""Map score → L1|L2|L3|noise|pool. Supply/equipment forced to L3 (P10)."""
from __future__ import annotations

from app.scoring.rules import is_construction_watch, is_noise, is_supply_watch, score_title


def assign_tier(title: str) -> tuple[str, int, str, bool]:
    score, reasons, uzk = score_title(title)
    reason_s = "; ".join(reasons) if reasons else "none"

    if is_supply_watch(title):
        if "supply_l3" not in reason_s:
            reason_s = f"{reason_s}; supply_l3" if reason_s != "none" else "supply_l3"
        return "L3", score, reason_s, uzk

    if is_construction_watch(title):
        if "build_ctrl_l3" not in reason_s:
            reason_s = f"{reason_s}; build_ctrl_l3" if reason_s != "none" else "build_ctrl_l3"
        return "L3", score, reason_s, uzk

    if is_noise(title, score, reasons):
        return "noise", score, reason_s, uzk

    # L1: score >= 6 OR uzk service with score >= 4
    if score >= 6 or (uzk and score >= 4):
        return "L1", score, reason_s, uzk
    if 4 <= score <= 5:
        return "L2", score, reason_s, uzk
    if 2 <= score <= 3:
        return "L3", score, reason_s, uzk
    return "pool", score, reason_s, uzk

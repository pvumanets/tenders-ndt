"""Map score → L1|L2|L3|noise|pool."""
from __future__ import annotations

from app.scoring.rules import is_noise, score_title


def assign_tier(title: str) -> tuple[str, int, str, bool]:
    score, reasons, uzk = score_title(title)
    reason_s = "; ".join(reasons) if reasons else "none"

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

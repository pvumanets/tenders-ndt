import { describe, expect, it } from "vitest";
import type { InboxLot } from "../types";
import { effectiveTier } from "./format";

/** Mirrors LotBoard bucketing without mounting MUI. */
function boardBuckets(lots: InboxLot[]) {
  const visible = lots.filter((l) => !l.board_hidden);
  const live = visible.filter((l) => !l.deadline_expired);
  const expired = visible
    .filter((l) => l.deadline_expired)
    .slice()
    .sort((a, b) => b.deadline_msk.localeCompare(a.deadline_msk) || a.tender_id.localeCompare(b.tender_id));
  const byTier = (tier: string) => live.filter((l) => effectiveTier(l) === tier);
  return {
    L1: byTier("L1").map((l) => l.tender_id),
    L2: byTier("L2").map((l) => l.tender_id),
    L3: byTier("L3").map((l) => l.tender_id),
    expired: expired.map((l) => l.tender_id),
  };
}

function lot(partial: Partial<InboxLot> & Pick<InboxLot, "tender_id" | "tier">): InboxLot {
  return {
    title: "t",
    customer_name: "",
    score: 5,
    manual_tier: null,
    viewed: false,
    board_hidden: false,
    deadline_expired: false,
    deadline_msk: "2026-08-28",
    ingested_at: "2026-08-01",
    price_rub: null,
    location: "",
    status: "",
    fit_reason: "",
    contact_name: null,
    contact_phone: null,
    contact_email: null,
    url: "",
    source_platform_id: "rostender",
    documents: [],
    rules_tier: null,
    ai_reviewed: false,
    ai_tier: null,
    ai_reason_ru: "",
    ai_error: null,
    ai_wrong: false,
    ...partial,
  };
}

describe("boardBuckets P8", () => {
  it("keeps expired out of live columns and sorts freshest first", () => {
    const buckets = boardBuckets([
      lot({ tender_id: "live", tier: "L1", deadline_msk: "2026-08-28" }),
      lot({
        tender_id: "old",
        tier: "L1",
        deadline_expired: true,
        deadline_msk: "2026-08-20",
      }),
      lot({
        tender_id: "fresh",
        tier: "L2",
        deadline_expired: true,
        deadline_msk: "2026-08-26",
      }),
      lot({ tender_id: "hidden", tier: "L1", board_hidden: true }),
    ]);
    expect(buckets.L1).toEqual(["live"]);
    expect(buckets.L2).toEqual([]);
    expect(buckets.expired).toEqual(["fresh", "old"]);
  });
});

import { describe, expect, it } from "vitest";
import { normalizeLot } from "./inbox";
import { copy } from "../copy";

describe("normalizeLot P8 fields", () => {
  it("defaults board_hidden and deadline_expired to false", () => {
    const lot = normalizeLot({
      tender_id: "1",
      title: "t",
      score: 5,
      tier: "L1",
    });
    expect(lot.board_hidden).toBe(false);
    expect(lot.deadline_expired).toBe(false);
  });

  it("keeps server flags", () => {
    const lot = normalizeLot({
      tender_id: "1",
      title: "t",
      score: 5,
      tier: "L2",
      board_hidden: true,
      deadline_expired: true,
    });
    expect(lot.board_hidden).toBe(true);
    expect(lot.deadline_expired).toBe(true);
  });
});

describe("P8 copy", () => {
  it("has expired column and archive strings", () => {
    expect(copy.chip_expired).toBe("Просроченные");
    expect(copy.badge_deadline_expired).toBe("Срок подачи вышел");
    expect(copy.action_archive).toBe("В архив");
    expect(copy.action_restore_board).toBe("Вернуть на доску");
  });
});

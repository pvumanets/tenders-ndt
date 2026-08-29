import { describe, expect, it } from "vitest";
import { emptyGroupDraft } from "./SearchGroupDrawer";
import { copy } from "../../copy";

describe("SearchGroupDrawer limit", () => {
  it("defaults limit_n to 0 (no product cap)", () => {
    expect(emptyGroupDraft(3).limit_n).toBe(0);
    expect(emptyGroupDraft(3).sort_order).toBe(3);
  });

  it("exposes soft-stop hint without a hard 1000 max", () => {
    expect(copy.groups_limit_hint).toMatch(/0/);
    expect(copy.groups_limit_hint.toLowerCase()).not.toMatch(/1000/);
  });
});

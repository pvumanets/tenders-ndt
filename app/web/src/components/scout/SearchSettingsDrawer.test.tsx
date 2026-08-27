import { describe, expect, it } from "vitest";
import { emptySearchDraft } from "./SearchSettingsDrawer";
import { copy } from "../../copy";

describe("SearchSettingsDrawer limit (P11)", () => {
  it("defaults limit_n to 0 (no product cap)", () => {
    expect(emptySearchDraft(3).limit_n).toBe(0);
    expect(emptySearchDraft(3).sort_order).toBe(3);
  });

  it("exposes soft-stop hint without a hard 1000 max", () => {
    expect(copy.searches_limit_hint).toMatch(/0/);
    expect(copy.searches_limit_hint.toLowerCase()).not.toMatch(/1000/);
  });
});

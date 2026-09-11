import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import InboxCommandBar, {
  buildActiveFilterChips,
  countActiveGroupedFilters,
} from "./InboxCommandBar";
import { copy } from "../../copy";
import type { PriorityFilter } from "../../types";
import ThemeRegistry from "../../theme/ThemeRegistry";

afterEach(() => {
  cleanup();
});

const baseProps = {
  unreadOnly: false,
  onUnreadOnly: () => {},
  priority: [] as PriorityFilter,
  onPriority: () => {},
  search: "",
  onSearch: () => {},
  deadlinePreset: "any" as const,
  onDeadlinePreset: () => {},
  deadlineFrom: "",
  onDeadlineFrom: () => {},
  deadlineTo: "",
  onDeadlineTo: () => {},
  ingestedPreset: "any" as const,
  onIngestedPreset: () => {},
  ingestedFrom: "",
  onIngestedFrom: () => {},
  ingestedTo: "",
  onIngestedTo: () => {},
  view: "cards" as const,
  onView: () => {},
  aiState: "any" as const,
  onAiState: () => {},
  aiTriggerFilter: "any" as const,
  onAiTriggerFilter: () => {},
};
function renderBar(ui: React.ReactElement) {
  return render(<ThemeRegistry>{ui}</ThemeRegistry>);
}

describe("countActiveGroupedFilters / chips", () => {
  it("counts non-default grouped axes", () => {
    expect(
      countActiveGroupedFilters({
        priority: [],
        deadlinePreset: "any",
        ingestedPreset: "any",
        priceMinRub: null,
        platformsSelected: [],
        bitrixFilter: "any",
        aiState: "any",
        aiTriggerFilter: "any",
      }),
    ).toBe(0);
    expect(
      countActiveGroupedFilters({
        priority: ["L1"],
        deadlinePreset: "d7",
        ingestedPreset: "any",
        priceMinRub: 100_000,
        platformsSelected: ["rostender"],
        bitrixFilter: "in",
        aiState: "done",
        aiTriggerFilter: "auto",
      }),
    ).toBe(7);
  });

  it("builds chip labels for active axes", () => {
    const chips = buildActiveFilterChips({
      priority: ["L2"],
      deadlinePreset: "d14",
      ingestedPreset: "any",
      priceMinRub: null,
      platformsSelected: [],
      bitrixFilter: "any",
      aiState: "failed",
      aiTriggerFilter: "any",
    });
    expect(chips.map((c) => c.id)).toEqual(["priority", "deadline", "ai_state"]);
    expect(chips[2].label).toContain(copy.filter_ai_state_failed);
  });
});

describe("InboxCommandBar AI filters", () => {
  it("exposes AI state and trigger radios in filters menu", async () => {
    const user = userEvent.setup();
    const onAiState = vi.fn();
    const onAiTriggerFilter = vi.fn();
    renderBar(
      <InboxCommandBar
        {...baseProps}
        onAiState={onAiState}
        onAiTriggerFilter={onAiTriggerFilter}
      />,
    );
    await user.click(screen.getByRole("button", { name: copy.filter_menu }));
    const menu = screen.getByRole("presentation");
    expect(within(menu).getByText(copy.filter_ai_state_title)).toBeTruthy();
    expect(within(menu).getByText(copy.filter_ai_trigger_title)).toBeTruthy();
    await user.click(within(menu).getByLabelText(copy.filter_ai_state_failed));
    expect(onAiState).toHaveBeenCalledWith("failed");
  });
});

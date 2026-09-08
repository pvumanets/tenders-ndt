import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import InboxCommandBar, {
  buildActiveFilterChips,
  countActiveGroupedFilters,
} from "./InboxCommandBar";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";

afterEach(() => {
  cleanup();
});

const baseProps = {
  unreadOnly: false,
  onUnreadOnly: () => {},
  priority: [] as const,
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
        showAiReviewedFilter: false,
        aiReviewedOnly: false,
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
        showAiReviewedFilter: true,
        aiReviewedOnly: true,
      }),
    ).toBe(6);
  });

  it("builds chip labels for active axes", () => {
    const chips = buildActiveFilterChips({
      priority: ["L2"],
      deadlinePreset: "d14",
      ingestedPreset: "any",
      priceMinRub: null,
      platformsSelected: [],
      bitrixFilter: "any",
      showAiReviewedFilter: false,
      aiReviewedOnly: false,
    });
    expect(chips.map((c) => c.id)).toEqual(["priority", "deadline"]);
    expect(chips[0].label).toContain(copy.filter_priority_strong);
    expect(chips[1].label).toContain(copy.filter_deadline_14);
  });
});

describe("InboxCommandBar", () => {
  it("primary strip shows unread, filters, sort, view — not flat filter triggers", () => {
    const { container } = renderBar(
      <InboxCommandBar
        {...baseProps}
        priority={[]}
        sort="relevance"
        onSort={() => {}}
        priceMinRub={100_000}
        onPriceMinRub={() => {}}
      />,
    );
    expect(within(container).getByRole("button", { name: copy.filter_unread })).toBeInTheDocument();
    expect(within(container).getByRole("button", { name: copy.filter_menu })).toBeInTheDocument();
    expect(within(container).getByRole("button", { name: copy.sort_relevance })).toBeInTheDocument();
    expect(within(container).getByRole("button", { name: copy.view_cards })).toBeInTheDocument();
    expect(within(container).queryByRole("button", { name: copy.filter_deadline })).not.toBeInTheDocument();
    expect(within(container).queryByRole("button", { name: copy.filter_price })).not.toBeInTheDocument();
  });

  it("opens Фильтры with three section titles", async () => {
    const user = userEvent.setup();
    const { container } = renderBar(
      <InboxCommandBar
        {...baseProps}
        priority={[]}
        showAiReviewedFilter
        aiReviewedOnly={false}
        onAiReviewedOnly={() => {}}
        priceMinRub={null}
        onPriceMinRub={() => {}}
        platforms={[
          {
            platform_id: "rostender",
            name: "Ростендер",
            enabled: true,
            session: "ok",
          },
        ]}
        platformsSelected={[]}
        onPlatformsSelected={() => {}}
        bitrixFilter="any"
        onBitrixFilter={() => {}}
      />,
    );
    await user.click(within(container).getByRole("button", { name: copy.filter_menu }));
    expect(await screen.findByText(copy.filter_section_dates)).toBeInTheDocument();
    expect(screen.getByText(copy.filter_section_class)).toBeInTheDocument();
    expect(screen.getByText(copy.filter_section_source)).toBeInTheDocument();
    expect(screen.getByText(copy.filter_ai_reviewed)).toBeInTheDocument();
  });

  it("shows deadline chip and clear-all", async () => {
    const user = userEvent.setup();
    const onDeadlinePreset = vi.fn();
    const onPriority = vi.fn();
    const { container } = renderBar(
      <InboxCommandBar
        {...baseProps}
        priority={["L1"]}
        onPriority={onPriority}
        deadlinePreset="d7"
        onDeadlinePreset={onDeadlinePreset}
      />,
    );
    expect(
      within(container).getByText(
        copy.filter_chip_deadline.replace("{value}", copy.filter_deadline_7),
      ),
    ).toBeInTheDocument();
    const clearAll = within(container).getByRole("button", { name: copy.filter_chips_clear_all });
    await user.click(clearAll);
    expect(onPriority).toHaveBeenCalledWith([]);
    expect(onDeadlinePreset).toHaveBeenCalledWith("any");
  });

  it("does not show AI reviewed outside filters when hidden", () => {
    renderBar(<InboxCommandBar {...baseProps} priority={[]} />);
    expect(screen.queryByText(copy.filter_ai_reviewed)).not.toBeInTheDocument();
    expect(screen.queryByText(copy.action_ai_review)).not.toBeInTheDocument();
  });

  it("price filter show all clears min price from grouped popover", async () => {
    const user = userEvent.setup();
    const onPriceMinRub = vi.fn();
    const { container } = renderBar(
      <InboxCommandBar
        {...baseProps}
        priority={[]}
        priceMinRub={100_000}
        onPriceMinRub={onPriceMinRub}
        settingsMinPrice={100_000}
      />,
    );
    await user.click(within(container).getByRole("button", { name: copy.filter_menu }));
    await user.click(await screen.findByRole("button", { name: copy.filter_price_show_all }));
    expect(onPriceMinRub).toHaveBeenCalledWith(null);
  });

  it("price filter links to settings from grouped popover", async () => {
    const user = userEvent.setup();
    const onOpenSettings = vi.fn();
    const { container } = renderBar(
      <InboxCommandBar
        {...baseProps}
        priority={[]}
        priceMinRub={100_000}
        onPriceMinRub={() => {}}
        settingsMinPrice={100_000}
        onOpenSettings={onOpenSettings}
      />,
    );
    await user.click(within(container).getByRole("button", { name: copy.filter_menu }));
    await user.click(await screen.findByRole("button", { name: copy.filter_price_settings_link }));
    expect(onOpenSettings).toHaveBeenCalled();
  });

  it("sticks the whole filters+search block for the board scroll parent", () => {
    const { container } = renderBar(<InboxCommandBar {...baseProps} priority={[]} />);
    const root = container.firstElementChild as HTMLElement;
    expect(getComputedStyle(root).position).toBe("sticky");
  });

  it("calls onSort when sort mode toggled", async () => {
    const user = userEvent.setup();
    const onSort = vi.fn();
    const { container } = renderBar(
      <InboxCommandBar {...baseProps} priority={[]} sort="relevance" onSort={onSort} />,
    );
    await user.click(within(container).getByRole("button", { name: copy.sort_appeared }));
    expect(onSort).toHaveBeenCalledWith("appeared");
    await user.click(within(container).getByRole("button", { name: copy.sort_deadline }));
    expect(onSort).toHaveBeenCalledWith("deadline");
  });

  it("shows mark-all-viewed action when handlers provided", async () => {
    const user = userEvent.setup();
    const onCountUnreadInTab = vi.fn().mockResolvedValue(3);
    const onMarkAllUnreadInTab = vi.fn().mockResolvedValue(3);
    const { container } = renderBar(
      <InboxCommandBar
        {...baseProps}
        priority={[]}
        onCountUnreadInTab={onCountUnreadInTab}
        onMarkAllUnreadInTab={onMarkAllUnreadInTab}
      />,
    );
    await user.click(within(container).getByRole("button", { name: copy.action_mark_all_viewed }));
    expect(onCountUnreadInTab).toHaveBeenCalled();
    expect(await screen.findByText(copy.mark_all_viewed_confirm_title)).toBeInTheDocument();
    expect(
      screen.getByText(copy.mark_all_viewed_confirm_body.replace("{n}", "3")),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: copy.mark_all_viewed_confirm }));
    expect(onMarkAllUnreadInTab).toHaveBeenCalled();
  });
});

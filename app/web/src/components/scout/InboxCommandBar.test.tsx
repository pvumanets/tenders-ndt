import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import InboxCommandBar from "./InboxCommandBar";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";

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

describe("InboxCommandBar", () => {
  it("does not show AI reviewed checkbox or review button", () => {
    render(
      <ThemeRegistry>
        <InboxCommandBar {...baseProps} priority={[]} />
      </ThemeRegistry>,
    );
    expect(screen.queryByText(copy.filter_ai_reviewed)).not.toBeInTheDocument();
    expect(screen.queryByText(copy.action_ai_review)).not.toBeInTheDocument();
  });

  it("AI filter menu uses distinct title and checkbox label", async () => {
    const user = userEvent.setup();
    render(
      <ThemeRegistry>
        <InboxCommandBar
          {...baseProps}
          priority={[]}
          showAiReviewedFilter
          aiReviewedOnly={false}
          onAiReviewedOnly={() => {}}
        />
      </ThemeRegistry>,
    );
    await user.click(screen.getByRole("button", { name: copy.filter_ai_reviewed_trigger }));
    expect(screen.getByText(copy.filter_ai_reviewed_menu_title)).toBeInTheDocument();
    expect(screen.getByText(copy.filter_ai_reviewed)).toBeInTheDocument();
    expect(screen.getAllByText(copy.filter_ai_reviewed_trigger)).toHaveLength(1);
  });

  it("price filter menu show all clears min price", async () => {
    const user = userEvent.setup();
    const onPriceMinRub = vi.fn();
    render(
      <ThemeRegistry>
        <InboxCommandBar
          {...baseProps}
          priority={[]}
          priceMinRub={100_000}
          onPriceMinRub={onPriceMinRub}
          settingsMinPrice={100_000}
        />
      </ThemeRegistry>,
    );
    await user.click(screen.getByRole("button", { name: copy.filter_price }));
    await user.click(screen.getByRole("button", { name: copy.filter_price_show_all }));
    expect(onPriceMinRub).toHaveBeenCalledWith(null);
  });

  it("price filter menu links to settings", async () => {
    const user = userEvent.setup();
    const onOpenSettings = vi.fn();
    render(
      <ThemeRegistry>
        <InboxCommandBar
          {...baseProps}
          priority={[]}
          priceMinRub={100_000}
          onPriceMinRub={() => {}}
          settingsMinPrice={100_000}
          onOpenSettings={onOpenSettings}
        />
      </ThemeRegistry>,
    );
    await user.click(screen.getByRole("button", { name: copy.filter_price }));
    await user.click(screen.getByRole("button", { name: copy.filter_price_settings_link }));
    expect(onOpenSettings).toHaveBeenCalled();
  });

  it("sticks the whole filters+search block for the board scroll parent", () => {
    const { container } = render(
      <ThemeRegistry>
        <InboxCommandBar {...baseProps} priority={[]} />
      </ThemeRegistry>,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(getComputedStyle(root).position).toBe("sticky");
  });
});

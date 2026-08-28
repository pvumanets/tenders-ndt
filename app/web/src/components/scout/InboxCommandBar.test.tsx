import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
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
});

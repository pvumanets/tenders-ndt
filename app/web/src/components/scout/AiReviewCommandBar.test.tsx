import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";
import AiReviewCommandBar from "./AiReviewCommandBar";

afterEach(() => {
  cleanup();
});

describe("AiReviewCommandBar", () => {
  it("shows ETA progress while review is in progress", () => {
    render(
      <ThemeRegistry>
        <AiReviewCommandBar onAiReview={vi.fn()} aiDone={2} aiTotal={5} />
      </ThemeRegistry>,
    );
    expect(
      screen.getByText(copy.ai_eta_progress.replace("{n}", "2").replace("{m}", "5")),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: copy.action_ai_review })).toBeDisabled();
  });
});

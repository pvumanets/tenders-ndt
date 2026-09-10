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

  it("shows cap hint when idle", () => {
    render(
      <ThemeRegistry>
        <AiReviewCommandBar onAiReview={vi.fn()} />
      </ThemeRegistry>,
    );
    expect(screen.getByText(copy.ai_review_cap_hint)).toBeInTheDocument();
  });

  it("shows retry errors action when failures present", () => {
    const onRetry = vi.fn();
    render(
      <ThemeRegistry>
        <AiReviewCommandBar onAiReview={vi.fn()} onRetryErrors={onRetry} aiFailures={3} />
      </ThemeRegistry>,
    );
    expect(screen.getByRole("button", { name: copy.action_ai_retry_errors })).toBeInTheDocument();
    expect(screen.getByText(copy.ai_banner_failures.replace("{n}", "3"))).toBeInTheDocument();
  });
});

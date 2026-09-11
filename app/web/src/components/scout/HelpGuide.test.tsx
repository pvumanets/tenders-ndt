import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import HelpGuide from "./HelpGuide";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";

afterEach(() => {
  cleanup();
});

function renderHelp(props?: Partial<Parameters<typeof HelpGuide>[0]>) {
  return render(
    <ThemeRegistry>
      <HelpGuide
        focusCookies={props?.focusCookies}
        onOpenSettings={props?.onOpenSettings ?? (() => undefined)}
      />
    </ThemeRegistry>,
  );
}

describe("HelpGuide", () => {
  it("shows FAQ questions and lead without Scout", () => {
    renderHelp();
    expect(screen.getByText(copy.help_lead)).toBeInTheDocument();
    expect(screen.getByText(copy.help_faq_why_q)).toBeInTheDocument();
    expect(screen.getByText(copy.help_faq_session_q)).toBeInTheDocument();
    expect(screen.getByText(copy.help_faq_new_q)).toBeInTheDocument();
    expect(screen.getByText(copy.help_faq_trouble_q)).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\bScout\b/);
  });

  it("expands another FAQ on click", async () => {
    const user = userEvent.setup();
    renderHelp();
    expect(screen.getByText(copy.help_faq_why_a)).toBeVisible();
    await user.click(screen.getByText(copy.help_faq_day_q));
    expect(await screen.findByText(copy.help_faq_day_a1)).toBeVisible();
  });

  it("opens settings from session FAQ", async () => {
    const onOpenSettings = vi.fn();
    const user = userEvent.setup();
    renderHelp({ onOpenSettings, focusCookies: true });
    await user.click(screen.getByRole("button", { name: copy.help_open_settings }));
    expect(onOpenSettings).toHaveBeenCalledTimes(1);
  });

  it("opens session FAQ when focusCookies", async () => {
    const scrollIntoView = vi.fn();
    const orig = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = scrollIntoView;
    try {
      renderHelp({ focusCookies: true });
      expect(await screen.findByText(copy.help_faq_session_what)).toBeVisible();
      expect(document.getElementById("help-cookies")).toBeTruthy();
      await vi.waitFor(() => expect(scrollIntoView).toHaveBeenCalled());
    } finally {
      Element.prototype.scrollIntoView = orig;
    }
  });
});

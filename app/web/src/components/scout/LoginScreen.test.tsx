import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";
import LoginScreen from "./LoginScreen";

describe("LoginScreen", () => {
  it("shows login_error when submit fails", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, json: async () => ({}) }),
    );
    render(
      <ThemeRegistry>
        <LoginScreen onSuccess={() => undefined} />
      </ThemeRegistry>,
    );
    await user.type(screen.getByLabelText(copy.login_username), "demo");
    await user.type(screen.getByLabelText(copy.login_password), "nope");
    await user.click(screen.getByRole("button", { name: copy.login_submit }));
    expect(await screen.findByText(copy.login_error)).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});

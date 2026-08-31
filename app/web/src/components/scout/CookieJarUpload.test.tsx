import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";
import CookieJarUpload from "./CookieJarUpload";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("CookieJarUpload", () => {
  it("keeps paste textarea collapsed until toggle", async () => {
    const user = userEvent.setup();
    render(
      <ThemeRegistry>
        <CookieJarUpload platformId="rostender" locked={false} session="ok" onUploaded={vi.fn()} />
      </ThemeRegistry>,
    );
    expect(screen.getByText(copy.cookies_on_server)).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(copy.cookies_paste_placeholder)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: copy.cookies_paste }));
    expect(screen.getByPlaceholderText(copy.cookies_paste_placeholder)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: copy.cookies_paste_hide })).toBeInTheDocument();
  });

  it("shows missing caption without cookie filenames", () => {
    const { container } = render(
      <ThemeRegistry>
        <CookieJarUpload
          platformId="rostender"
          locked={false}
          session="missing"
          onUploaded={vi.fn()}
        />
      </ThemeRegistry>,
    );
    expect(screen.getByText(copy.cookies_missing)).toBeInTheDocument();
    expect(container.textContent?.toLowerCase() ?? "").not.toMatch(/cookies\./);
  });
});

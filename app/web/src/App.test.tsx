import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { copy } from "./copy";

afterEach(() => {
  vi.unstubAllGlobals();
});

function jsonResponse(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

describe("App inbox gate", () => {
  it("shows login, not lots, when inbox returns 401", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/api/me")) {
          return jsonResponse(200, { username: "digital", display_name: "Digital" });
        }
        if (url.includes("/api/inbox")) {
          return jsonResponse(401, { detail: "unauthorized" });
        }
        return jsonResponse(200, {});
      }),
    );

    render(<App />);

    expect(await screen.findByLabelText(copy.login_username)).toBeInTheDocument();
    expect(screen.queryByText(copy.tab_lots)).not.toBeInTheDocument();
    expect(screen.queryByText("УЗК труб")).not.toBeInTheDocument();
  });
});

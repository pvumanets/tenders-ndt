import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { copy } from "./copy";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

function jsonResponse(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

function stubApi() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo) => {
      const url = String(input);
      if (url.includes("/api/me")) {
        return jsonResponse(200, { username: "digital", display_name: "Digital" });
      }
      if (url.includes("/api/inbox")) {
        return jsonResponse(200, { items: [] });
      }
      if (url.includes("/api/status")) {
        return jsonResponse(200, {
          phase: "idle",
          running: false,
          pipeline: "manual",
          ai_review_done: 0,
          ai_review_total: 0,
        });
      }
      if (url.includes("/api/search-groups")) {
        return jsonResponse(200, {
          items: [
            {
              id: "g1",
              name: "методы",
              queries: ["ВИК"],
              exclude: [],
              limit_n: 0,
              in_queue: true,
              sort_order: 0,
            },
          ],
        });
      }
      if (url.includes("/api/platforms/") && url.includes("/cookies")) {
        return jsonResponse(404, { detail: "not_found" });
      }
      if (url.includes("/api/platforms")) {
        return jsonResponse(200, {
          items: [
            { platform_id: "rostender", name: copy.platform_rostender, enabled: true, session: "ok" },
          ],
        });
      }
      if (url.includes("/api/schedule")) {
        return jsonResponse(200, {
          enabled: true,
          time_msk: "07:00",
          last_fired_at: null,
          last_skip_reason: null,
          last_attempt_at: null,
          next_fire_at: null,
        });
      }
      return jsonResponse(200, {});
    }),
  );
}

describe("App inbox gate", () => {
  it("shows login, not tabs, when inbox returns 401", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/api/me") || url.includes("/api/inbox")) {
          return jsonResponse(401, { detail: "unauthorized" });
        }
        return jsonResponse(200, {});
      }),
    );

    render(<App />);

    expect(await screen.findByLabelText(copy.login_username)).toBeInTheDocument();
    expect(screen.queryByText(copy.tab_auto)).not.toBeInTheDocument();
    expect(screen.queryByText("УЗК труб")).not.toBeInTheDocument();
  });
});

describe("AppTabs", () => {
  it("defaults to Авторазбор without Start or AI review", async () => {
    stubApi();
    render(<App />);
    expect(await screen.findByText(copy.tab_auto)).toBeInTheDocument();
    expect(screen.getByText(copy.tab_manual)).toBeInTheDocument();
    expect(screen.getByText(copy.tab_settings)).toBeInTheDocument();
    expect(screen.queryByText(copy.tab_lots)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: copy.run_start })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: copy.action_ai_review })).not.toBeInTheDocument();
    expect(screen.getByText(copy.auto_mail_hint)).toBeInTheDocument();
  });

  it("shows Start and AI review on Ручной, settings controls on Настройки", async () => {
    stubApi();
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText(copy.tab_auto);
    await user.click(screen.getByRole("tab", { name: copy.tab_manual }));
    expect(await screen.findByRole("button", { name: copy.run_start })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: copy.action_ai_review })).toBeInTheDocument();
    expect(screen.getByText(copy.manual_no_mail_hint)).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: copy.tab_settings }));
    expect(await screen.findByText(copy.settings_section_schedule)).toBeInTheDocument();
    expect(screen.getByText(copy.settings_section_platforms)).toBeInTheDocument();
    expect(screen.getByText(copy.settings_section_groups)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: copy.cookies_submit }).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: copy.run_start })).not.toBeInTheDocument();
  });

  it("shows AI ETA on Ручной and has no Bitrix chrome", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/api/me")) {
          return jsonResponse(200, { username: "digital", display_name: "Digital" });
        }
        if (url.includes("/api/inbox")) {
          return jsonResponse(200, { items: [] });
        }
        if (url.includes("/api/status")) {
          return jsonResponse(200, {
            phase: "idle",
            running: false,
            pipeline: "manual",
            ai_review_done: 1,
            ai_review_total: 4,
          });
        }
        if (url.includes("/api/search-groups")) {
          return jsonResponse(200, {
            items: [
              {
                id: "g1",
                name: "методы",
                queries: ["ВИК"],
                exclude: [],
                limit_n: 0,
                in_queue: true,
                sort_order: 0,
              },
            ],
          });
        }
        if (url.includes("/api/platforms/") && url.includes("/cookies")) {
          return jsonResponse(404, { detail: "not_found" });
        }
        if (url.includes("/api/platforms")) {
          return jsonResponse(200, {
            items: [
              {
                platform_id: "rostender",
                name: copy.platform_rostender,
                enabled: true,
                session: "ok",
              },
            ],
          });
        }
        if (url.includes("/api/schedule")) {
          return jsonResponse(200, {
            enabled: true,
            time_msk: "07:00",
            last_fired_at: null,
            last_skip_reason: null,
            last_attempt_at: null,
            next_fire_at: null,
          });
        }
        return jsonResponse(200, {});
      }),
    );
    const user = userEvent.setup();
    const { container } = render(<App />);
    await screen.findByText(copy.tab_auto);
    expect(container.textContent?.toLowerCase() ?? "").not.toMatch(/bitrix/);
    expect(container.textContent?.toLowerCase() ?? "").not.toMatch(/\bcrm\b/);
    await user.click(screen.getByRole("tab", { name: copy.tab_manual }));
    expect(
      await screen.findByText(copy.ai_eta_progress.replace("{n}", "1").replace("{m}", "4")),
    ).toBeInTheDocument();
  });

  it("keeps polling status when schedule GET fails", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const fetchMock = vi.fn(async (input: RequestInfo) => {
      const url = String(input);
      if (url.includes("/api/me")) {
        return jsonResponse(200, { username: "digital", display_name: "Digital" });
      }
      if (url.includes("/api/inbox")) {
        return jsonResponse(200, { items: [] });
      }
      if (url.includes("/api/status")) {
        return jsonResponse(200, {
          phase: "idle",
          running: false,
          pipeline: "manual",
          ai_review_done: 0,
          ai_review_total: 0,
        });
      }
      if (url.includes("/api/search-groups")) {
        return jsonResponse(200, { items: [] });
      }
      if (url.includes("/api/platforms")) {
        return jsonResponse(200, { items: [] });
      }
      if (url.includes("/api/schedule")) {
        return jsonResponse(404, { detail: "not_found" });
      }
      return jsonResponse(200, {});
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    expect(await screen.findByText(copy.tab_auto)).toBeInTheDocument();
    const statusBefore = fetchMock.mock.calls.filter((call) =>
      String(call[0]).includes("/api/status"),
    ).length;
    expect(statusBefore).toBeGreaterThan(0);

    await vi.advanceTimersByTimeAsync(8000);
    const statusAfter = fetchMock.mock.calls.filter((call) =>
      String(call[0]).includes("/api/status"),
    ).length;
    expect(statusAfter).toBeGreaterThan(statusBefore);
  });
});

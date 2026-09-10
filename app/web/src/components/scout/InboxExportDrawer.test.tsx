import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import InboxCommandBar from "./InboxCommandBar";
import InboxExportDrawer from "./InboxExportDrawer";
import { copy } from "../../copy";
import { AI_REVIEW_EXPORT_PRESET } from "../../lib/inbox-export";
import ThemeRegistry from "../../theme/ThemeRegistry";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const baseProps = {
  unreadOnly: false,
  onUnreadOnly: () => {},
  priority: [] as import("../../types").PriorityFilter,
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

function renderUi(ui: React.ReactElement) {
  return render(<ThemeRegistry>{ui}</ThemeRegistry>);
}

describe("InboxCommandBar export", () => {
  it("renders Export button when onExport is set", async () => {
    const onExport = vi.fn();
    const user = userEvent.setup();
    renderUi(<InboxCommandBar {...baseProps} onExport={onExport} />);
    const btn = screen.getByRole("button", { name: copy.export_button });
    await user.click(btn);
    expect(onExport).toHaveBeenCalledTimes(1);
  });

  it("hides Export when onExport is omitted", () => {
    renderUi(<InboxCommandBar {...baseProps} />);
    expect(screen.queryByRole("button", { name: copy.export_button })).toBeNull();
  });
});

describe("InboxExportDrawer", () => {
  it("defaults to AI preset and disables download when N=0", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/inbox?")) {
          return new Response(JSON.stringify({ items: [], total: 0 }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        return new Response("nope", { status: 500 });
      }),
    );

    renderUi(
      <InboxExportDrawer
        open
        onClose={() => {}}
        prefill={{ tier: "fit", ai_reviewed: true, ai_trigger: "auto" }}
      />,
    );

    expect(await screen.findByText(copy.export_empty_title)).toBeTruthy();
    const download = screen.getByRole("button", { name: copy.export_download });
    expect(download).toBeDisabled();

    for (const key of AI_REVIEW_EXPORT_PRESET) {
      // RU labels from catalog — at least tender_id / title present
      void key;
    }
    expect(screen.getByLabelText("Id")).toBeChecked();
    expect(screen.getByLabelText("Почему ИИ")).toBeChecked();
  });

  it("enables download when count > 0", async () => {
    const user = userEvent.setup();
    let exported = false;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/api/inbox?") && (!init || !init.method || init.method === "GET")) {
          return new Response(JSON.stringify({ items: [{ tender_id: "1" }], total: 2 }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        if (url.includes("/api/inbox/export") && init?.method === "POST") {
          exported = true;
          return new Response("Id\n1\n", {
            status: 200,
            headers: {
              "Content-Type": "text/csv",
              "Content-Disposition": 'attachment; filename="inbox-export-2026-09-10-0900.csv"',
            },
          });
        }
        return new Response("nope", { status: 500 });
      }),
    );

    // jsdom may not implement URL.createObjectURL
    const createObjectURL = vi.fn(() => "blob:mock");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", {
      ...URL,
      createObjectURL,
      revokeObjectURL,
    });

    renderUi(
      <InboxExportDrawer
        open
        onClose={() => {}}
        prefill={{ tier: "fit" }}
      />,
    );

    expect(await screen.findByText(copy.export_count.replace("{n}", "2"))).toBeTruthy();
    const download = screen.getByRole("button", { name: copy.export_download });
    expect(download).not.toBeDisabled();
    await user.click(download);
    expect(exported).toBe(true);
  });
});

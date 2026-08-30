import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";
import type { PlatformRow, SearchGroup, TechStatus } from "../../types";
import ManualRunControls from "./ManualRunControls";

afterEach(() => {
  cleanup();
});

const idle: TechStatus = {
  phase: "idle",
  phase_label: copy.phase_idle,
  running: false,
  pipeline: "manual",
  list_done: 0,
  list_total: 1000,
  cards_done: 0,
  cards_total: 0,
  counters: { L1: 0, L2: 0, L3: 0, noise: 0 },
  run_report: { new: 0, already: 0, updated: 0, expired: 0 },
  ai_failures: 0,
  ai_review_done: 0,
  ai_review_total: 0,
  http_retries: 0,
  session: "ok",
  run_dir: "/tmp/run",
  queue: [],
  queue_index: 0,
  queue_total: 0,
  current_search_name: "",
  log: [],
};

function renderControls(
  status: TechStatus,
  extra?: Partial<Parameters<typeof ManualRunControls>[0]>,
) {
  const onStart = extra?.onStart ?? vi.fn();
  const onStop = extra?.onStop ?? vi.fn();
  render(
    <ThemeRegistry>
      <ManualRunControls
        status={status}
        queuedGroups={extra?.queuedGroups ?? 1}
        enabledPlatforms={extra?.enabledPlatforms ?? 1}
        busy={extra?.busy}
        error={extra?.error}
        onStart={onStart}
        onStop={onStop}
      />
    </ThemeRegistry>,
  );
  return { onStart, onStop };
}

describe("ManualRunControls", () => {
  it("renders controls section and start/stop", async () => {
    const user = userEvent.setup();
    const { onStart, onStop } = renderControls(idle);
    expect(screen.getByText(copy.run_section_controls)).toBeInTheDocument();
    const start = screen.getByRole("button", { name: copy.run_start });
    const stop = screen.getByRole("button", { name: copy.run_stop });
    expect(start).toBeEnabled();
    expect(stop).toBeDisabled();
    await user.click(start);
    expect(onStart).toHaveBeenCalledTimes(1);
    expect(onStop).not.toHaveBeenCalled();
  });

  it("disables start when the queue is empty", () => {
    renderControls(idle, { queuedGroups: 0, enabledPlatforms: 1 });
    expect(screen.getByRole("button", { name: copy.run_start })).toBeDisabled();
    expect(screen.getByText(copy.empty_manual_queue)).toBeInTheDocument();
  });

  it("enables stop while running", () => {
    renderControls({ ...idle, running: true, queue_total: 2, queue_index: 0 });
    expect(screen.getByRole("button", { name: copy.run_start })).toBeDisabled();
    expect(screen.getByRole("button", { name: copy.run_stop })).toBeEnabled();
  });

  it("shows run report only when done", () => {
    renderControls({
      ...idle,
      phase: "done",
      phase_label: copy.phase_done,
      run_report: { new: 1, already: 2, updated: 3, expired: 4 },
    });
    expect(screen.getByText(`${copy.run_report_new}: 1`)).toBeInTheDocument();
  });

  it("hides run report while idle", () => {
    renderControls({
      ...idle,
      run_report: { new: 1, already: 2, updated: 3, expired: 4 },
    });
    expect(screen.queryByText(`${copy.run_report_new}: 1`)).not.toBeInTheDocument();
  });
});

export const idleStatus = idle;
export const sampleGroups: SearchGroup[] = [
  {
    id: "g-methods",
    name: "методы",
    queries: ["неразрушающий"],
    exclude: [],
    limit_n: 0,
    in_queue: true,
    sort_order: 1,
  },
  {
    id: "g-services",
    name: "услуги НК",
    queries: ["ВИК", "ПВК"],
    exclude: [],
    limit_n: 0,
    in_queue: false,
    sort_order: 2,
  },
];
export const samplePlatforms: PlatformRow[] = [
  { platform_id: "rostender", name: copy.platform_rostender, enabled: true, session: "ok" },
  {
    platform_id: "tender-pro",
    name: copy.platform_tender_pro,
    enabled: true,
    session: "list_without_login",
  },
  { platform_id: "roseltorg", name: copy.platform_roseltorg, enabled: false, session: "missing" },
];

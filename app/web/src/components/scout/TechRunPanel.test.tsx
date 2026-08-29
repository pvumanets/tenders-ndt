import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";
import type { PlatformRow, SearchGroup, TechStatus } from "../../types";
import TechRunPanel from "./TechRunPanel";

afterEach(() => {
  cleanup();
});

const idle: TechStatus = {
  phase: "idle",
  phase_label: copy.phase_idle,
  running: false,
  list_done: 0,
  list_total: 1000,
  cards_done: 0,
  cards_total: 0,
  counters: { L1: 0, L2: 0, L3: 0, noise: 0 },
  run_report: { new: 0, already: 0, updated: 0, expired: 0 },
  ai_failures: 0,
  http_retries: 0,
  session: "ok",
  run_dir: "/tmp/run",
  queue: [],
  queue_index: 0,
  queue_total: 0,
  current_search_name: "",
  log: [],
};

const methods: SearchGroup = {
  id: "g-methods",
  name: "методы",
  queries: ["неразрушающий"],
  exclude: [],
  limit_n: 0,
  in_queue: true,
  sort_order: 1,
};

const services: SearchGroup = {
  id: "g-services",
  name: "услуги НК",
  queries: ["ВИК", "ПВК"],
  exclude: [],
  limit_n: 0,
  in_queue: false,
  sort_order: 2,
};

const platforms: PlatformRow[] = [
  {
    platform_id: "rostender",
    name: copy.platform_rostender,
    enabled: true,
    session: "ok",
  },
  {
    platform_id: "tender-pro",
    name: copy.platform_tender_pro,
    enabled: true,
    session: "list_without_login",
  },
  {
    platform_id: "roseltorg",
    name: copy.platform_roseltorg,
    enabled: false,
    session: "missing",
  },
];

function renderPanel(
  status: TechStatus,
  extra?: Partial<Parameters<typeof TechRunPanel>[0]>,
) {
  const onStart = extra?.onStart ?? vi.fn();
  const onStop = extra?.onStop ?? vi.fn();
  const onToggleQueue = extra?.onToggleQueue ?? vi.fn();
  const onTogglePlatform = extra?.onTogglePlatform ?? vi.fn();
  const onSaveGroup = extra?.onSaveGroup ?? vi.fn().mockResolvedValue(undefined);
  const onDeleteGroup = extra?.onDeleteGroup ?? vi.fn();
  render(
    <ThemeRegistry>
      <TechRunPanel
        status={status}
        groups={extra?.groups ?? [methods, services]}
        platforms={extra?.platforms ?? platforms}
        busy={extra?.busy}
        error={extra?.error}
        groupError={extra?.groupError}
        onStart={onStart}
        onStop={onStop}
        onToggleQueue={onToggleQueue}
        onTogglePlatform={onTogglePlatform}
        onSaveGroup={onSaveGroup}
        onDeleteGroup={onDeleteGroup}
      />
    </ThemeRegistry>,
  );
  return { onStart, onStop, onToggleQueue, onTogglePlatform, onSaveGroup, onDeleteGroup };
}

describe("TechRunPanel", () => {
  it("renders four W-run section titles", () => {
    renderPanel(idle);
    expect(screen.getByText(copy.run_section_controls)).toBeInTheDocument();
    expect(screen.getByText(copy.run_section_groups)).toBeInTheDocument();
    expect(screen.getByText(copy.run_section_platforms)).toBeInTheDocument();
    expect(screen.getByText(copy.run_section_diagnostics)).toBeInTheDocument();
  });

  it("keeps diagnostics collapsed and run path out of primary flow", () => {
    renderPanel(idle);
    expect(screen.queryByDisplayValue("/tmp/run")).not.toBeInTheDocument();
    expect(screen.queryByText(copy.run_path_label)).not.toBeInTheDocument();
  });

  it("opens group drawer without platform field", async () => {
    const user = userEvent.setup();
    renderPanel(idle);
    await user.click(screen.getAllByRole("button", { name: copy.groups_edit })[0]);
    expect(screen.getByText(copy.groups_drawer_title)).toBeInTheDocument();
    expect(screen.getByLabelText(copy.groups_name)).toHaveValue(methods.name);
    expect(screen.getByLabelText(copy.groups_queries)).toHaveValue("неразрушающий");
    expect(screen.queryByLabelText(/Площадка/i)).not.toBeInTheDocument();
  });

  it("saves draft with minus phrases", async () => {
    const user = userEvent.setup();
    const { onSaveGroup } = renderPanel(idle, {
      groups: [{ ...methods, exclude: ["кровля"] }],
    });
    await user.click(screen.getAllByRole("button", { name: copy.groups_edit })[0]);
    expect(screen.getByLabelText(copy.groups_exclude)).toHaveValue("кровля");
    await user.clear(screen.getByLabelText(copy.groups_exclude));
    await user.type(screen.getByLabelText(copy.groups_exclude), "ЗАГС\nшкола");
    await user.click(screen.getByRole("button", { name: copy.groups_save }));
    expect(onSaveGroup).toHaveBeenCalledWith("g-methods", {
      name: methods.name,
      queries: ["неразрушающий"],
      exclude: ["ЗАГС", "школа"],
      limit_n: 0,
      in_queue: true,
      sort_order: 1,
    });
  });

  it("enables start when a group and platform are queued", async () => {
    const user = userEvent.setup();
    const { onStart, onStop } = renderPanel(idle);
    const start = screen.getByRole("button", { name: copy.run_start });
    const stop = screen.getByRole("button", { name: copy.run_stop });
    expect(start).toBeEnabled();
    expect(stop).toBeDisabled();
    await user.click(start);
    expect(onStart).toHaveBeenCalledTimes(1);
    expect(onStop).not.toHaveBeenCalled();
  });

  it("disables start when the queue is empty", () => {
    renderPanel(idle, {
      groups: [
        { ...methods, in_queue: false },
        { ...services, in_queue: false },
      ],
    });
    expect(screen.getByRole("button", { name: copy.run_start })).toBeDisabled();
    expect(screen.getByText(copy.run_queue_empty)).toBeInTheDocument();
    expect(screen.getByText(copy.groups_none_queued)).toBeInTheDocument();
  });

  it("disables start when no platforms enabled", () => {
    renderPanel(idle, {
      platforms: platforms.map((row) => ({ ...row, enabled: false })),
    });
    expect(screen.getByRole("button", { name: copy.run_start })).toBeDisabled();
    expect(screen.getByText(copy.run_queue_empty)).toBeInTheDocument();
    expect(screen.getByText(copy.platforms_none_enabled)).toBeInTheDocument();
    expect(screen.getByText(copy.platforms_none_enabled_body)).toBeInTheDocument();
  });

  it("enables stop while running", () => {
    renderPanel({ ...idle, running: true, queue_total: 2, queue_index: 0 });
    expect(screen.getByRole("button", { name: copy.run_start })).toBeDisabled();
    expect(screen.getByRole("button", { name: copy.run_stop })).toBeEnabled();
  });

  it("shows session labels without cookie filenames", () => {
    renderPanel(idle);
    expect(screen.getByText(`${copy.platform_tender_pro}: ${copy.session_status_list_without_login}`)).toBeInTheDocument();
    expect(screen.queryByText(/cookies\.tender-pro/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/cookies\.roseltorg/i)).not.toBeInTheDocument();
  });

  it("shows run report only when done", () => {
    renderPanel({
      ...idle,
      phase: "done",
      phase_label: copy.phase_done,
      run_report: { new: 1, already: 2, updated: 3, expired: 4 },
    });
    expect(screen.getByText(`${copy.run_report_new}: 1`)).toBeInTheDocument();
    expect(screen.getByText(`${copy.run_report_already}: 2`)).toBeInTheDocument();
    expect(screen.getByText(`${copy.run_report_updated}: 3`)).toBeInTheDocument();
    expect(screen.getByText(`${copy.run_report_expired}: 4`)).toBeInTheDocument();
  });

  it("hides run report while idle", () => {
    renderPanel({
      ...idle,
      run_report: { new: 1, already: 2, updated: 3, expired: 4 },
    });
    expect(screen.queryByText(`${copy.run_report_new}: 1`)).not.toBeInTheDocument();
  });

  it("toggles group queue and platform enable", async () => {
    const user = userEvent.setup();
    const { onToggleQueue, onTogglePlatform } = renderPanel(idle);
    await user.click(screen.getByLabelText(`${copy.groups_queue}: ${services.name}`));
    expect(onToggleQueue).toHaveBeenCalledWith(services, true);
    await user.click(screen.getByLabelText(`${copy.platform_participate}: ${copy.platform_roseltorg}`));
    expect(onTogglePlatform).toHaveBeenCalledWith(platforms[2], true);
  });
});

import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";
import type { ScheduleSettings, TechStatus } from "../../types";
import SettingsPanel from "./SettingsPanel";
import { sampleGroups, samplePlatforms } from "./ManualRunControls.test";

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

const schedule: ScheduleSettings = {
  enabled: true,
  time_msk: "07:00",
  last_fired_at: null,
  last_skip_reason: null,
  last_attempt_at: null,
  next_fire_at: null,
};

function renderSettings(extra?: Partial<Parameters<typeof SettingsPanel>[0]>) {
  const onToggleQueue = extra?.onToggleQueue ?? vi.fn();
  const onTogglePlatform = extra?.onTogglePlatform ?? vi.fn();
  const onSaveGroup = extra?.onSaveGroup ?? vi.fn().mockResolvedValue(undefined);
  const onDeleteGroup = extra?.onDeleteGroup ?? vi.fn();
  render(
    <ThemeRegistry>
      <SettingsPanel
        status={extra?.status ?? idle}
        schedule={extra?.schedule ?? schedule}
        groups={extra?.groups ?? sampleGroups}
        platforms={extra?.platforms ?? samplePlatforms}
        locked={extra?.locked}
        groupError={extra?.groupError}
        onScheduleSaved={extra?.onScheduleSaved ?? vi.fn()}
        onToggleQueue={onToggleQueue}
        onTogglePlatform={onTogglePlatform}
        onSaveGroup={onSaveGroup}
        onDeleteGroup={onDeleteGroup}
        onCookieSession={extra?.onCookieSession ?? vi.fn()}
      />
    </ThemeRegistry>,
  );
  return { onToggleQueue, onTogglePlatform, onSaveGroup };
}

describe("SettingsPanel", () => {
  it("renders schedule, platforms, groups, cookie upload and collapsed diagnostics", () => {
    renderSettings();
    expect(screen.getByText(copy.settings_section_schedule)).toBeInTheDocument();
    expect(screen.getByText(copy.settings_section_platforms)).toBeInTheDocument();
    expect(screen.getByText(copy.settings_section_groups)).toBeInTheDocument();
    expect(screen.getByText(copy.settings_section_diagnostics)).toBeInTheDocument();
    expect(screen.getByLabelText(copy.schedule_time)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: copy.cookies_submit })).not.toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: copy.cookies_upload }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: copy.cookies_paste }).length).toBeGreaterThan(0);
    expect(screen.queryByPlaceholderText(copy.cookies_paste_placeholder)).not.toBeInTheDocument();
    expect(screen.queryByDisplayValue("/tmp/run")).not.toBeInTheDocument();
    expect(screen.queryByText(copy.run_path_label)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: copy.run_start })).not.toBeInTheDocument();
  });

  it("opens group drawer without platform field", async () => {
    const user = userEvent.setup();
    renderSettings();
    await user.click(screen.getAllByRole("button", { name: copy.groups_edit })[0]);
    expect(screen.getByText(copy.groups_drawer_title)).toBeInTheDocument();
    expect(screen.getByLabelText(copy.groups_name)).toHaveValue("методы");
    expect(screen.queryByLabelText(/Площадка/i)).not.toBeInTheDocument();
  });

  it(
    "saves draft with minus phrases",
    async () => {
      const user = userEvent.setup();
      const { onSaveGroup } = renderSettings({
        groups: [{ ...sampleGroups[0], exclude: ["кровля"] }],
      });
      await user.click(screen.getAllByRole("button", { name: copy.groups_edit })[0]);
      expect(screen.getByLabelText(copy.groups_exclude)).toHaveValue("кровля");
      await user.clear(screen.getByLabelText(copy.groups_exclude));
      await user.type(screen.getByLabelText(copy.groups_exclude), "ЗАГС\nшкола");
      await user.click(screen.getByRole("button", { name: copy.groups_save }));
      expect(onSaveGroup).toHaveBeenCalledWith("g-methods", {
        name: "методы",
        queries: ["неразрушающий"],
        exclude: ["ЗАГС", "школа"],
        limit_n: 0,
        in_queue: true,
        sort_order: 1,
      });
    },
    15_000,
  );

  it("shows session labels without cookie filenames", () => {
    renderSettings();
    expect(
      screen.getByText(`${copy.platform_tender_pro}: ${copy.session_status_list_without_login}`),
    ).toBeInTheDocument();
    expect(screen.queryByText(/cookies\.tender-pro/i)).not.toBeInTheDocument();
  });

  it("toggles group queue and platform enable", async () => {
    const user = userEvent.setup();
    const { onToggleQueue, onTogglePlatform } = renderSettings();
    await user.click(screen.getByLabelText(`${copy.groups_queue}: услуги НК`));
    expect(onToggleQueue).toHaveBeenCalledWith(sampleGroups[1], true);
    await user.click(screen.getByLabelText(`${copy.platform_participate}: ${copy.platform_roseltorg}`));
    expect(onTogglePlatform).toHaveBeenCalledWith(samplePlatforms[2], true);
  });

  it("locks schedule and cookies while running", () => {
    renderSettings({ locked: true });
    expect(screen.getByRole("button", { name: copy.schedule_save })).toBeDisabled();
    expect(screen.getAllByRole("button", { name: copy.cookies_upload })[0]).toBeDisabled();
    expect(screen.getAllByRole("button", { name: copy.cookies_paste })[0]).toBeDisabled();
  });
});

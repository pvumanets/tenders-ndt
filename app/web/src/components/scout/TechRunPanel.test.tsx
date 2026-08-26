import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";
import type { NamedSearch, TechStatus } from "../../types";
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
  session: "ok",
  run_dir: "",
  queue: [],
  queue_index: 0,
  queue_total: 0,
  current_search_name: "",
  log: [],
};

const rostender: NamedSearch = {
  id: "s-rt",
  name: "РосТендер НК",
  platform_id: "rostender",
  queries: ["неразрушающий"],
  limit_n: 1000,
  in_queue: true,
  sort_order: 0,
};

const tenderPro: NamedSearch = {
  id: "s-tp",
  name: "Tender.Pro НК",
  platform_id: "tender-pro",
  queries: ["ВИК", "ПВК"],
  limit_n: 1000,
  in_queue: false,
  sort_order: 1,
};

function renderPanel(
  status: TechStatus,
  extra?: Partial<Parameters<typeof TechRunPanel>[0]>,
) {
  const onStart = extra?.onStart ?? vi.fn();
  const onStop = extra?.onStop ?? vi.fn();
  const onToggleQueue = extra?.onToggleQueue ?? vi.fn();
  const onSaveSearch = extra?.onSaveSearch ?? vi.fn().mockResolvedValue(undefined);
  const onDeleteSearch = extra?.onDeleteSearch ?? vi.fn();
  render(
    <ThemeRegistry>
      <TechRunPanel
        status={status}
        searches={extra?.searches ?? [rostender, tenderPro]}
        busy={extra?.busy}
        error={extra?.error}
        searchError={extra?.searchError}
        onStart={onStart}
        onStop={onStop}
        onToggleQueue={onToggleQueue}
        onSaveSearch={onSaveSearch}
        onDeleteSearch={onDeleteSearch}
      />
    </ThemeRegistry>,
  );
  return { onStart, onStop, onToggleQueue, onSaveSearch, onDeleteSearch };
}

describe("TechRunPanel", () => {
  it("opens search settings drawer on edit", async () => {
    const user = userEvent.setup();
    renderPanel(idle);
    await user.click(screen.getAllByRole("button", { name: copy.searches_edit })[0]);
    expect(screen.getByText(copy.searches_drawer_title)).toBeInTheDocument();
    expect(screen.getByLabelText(copy.searches_name)).toHaveValue(rostender.name);
    expect(screen.getByLabelText(copy.searches_queries)).toHaveValue("неразрушающий");
  });

  it("enables start when a search is queued, even without cookies", async () => {
    const user = userEvent.setup();
    const { onStart, onStop } = renderPanel({ ...idle, session: "missing" });
    const start = screen.getByRole("button", { name: copy.run_start });
    const stop = screen.getByRole("button", { name: copy.run_stop });
    expect(start).toBeEnabled();
    expect(stop).toBeDisabled();
    await user.click(start);
    expect(onStart).toHaveBeenCalledTimes(1);
    expect(onStop).not.toHaveBeenCalled();
  });

  it("disables start when the queue is empty", () => {
    renderPanel(idle, { searches: [{ ...rostender, in_queue: false }, tenderPro] });
    expect(screen.getByRole("button", { name: copy.run_start })).toBeDisabled();
    expect(screen.getByText(copy.run_error_empty_queue)).toBeInTheDocument();
  });

  it("enables stop while running", () => {
    renderPanel({ ...idle, running: true });
    expect(screen.getByRole("button", { name: copy.run_start })).toBeDisabled();
    expect(screen.getByRole("button", { name: copy.run_stop })).toBeEnabled();
  });

  it("calls stop while running and shows error copy", async () => {
    const user = userEvent.setup();
    const { onStop } = renderPanel(
      { ...idle, running: true },
      { error: copy.run_error_already },
    );
    await user.click(screen.getByRole("button", { name: copy.run_stop }));
    expect(onStop).toHaveBeenCalledTimes(1);
    expect(screen.getByText(copy.run_error_already)).toBeInTheDocument();
    expect(screen.queryByText("Старт и стоп прогона в этом экране отключены")).not.toBeInTheDocument();
  });

  it("shows empty_queue copy from start error", () => {
    renderPanel(idle, { error: copy.run_error_empty_queue });
    expect(screen.getAllByText(copy.run_error_empty_queue).length).toBeGreaterThan(0);
  });

  it("keeps query and limit off the start button and in the search row", () => {
    renderPanel(idle);
    expect(screen.queryByLabelText(/query/i)).not.toBeInTheDocument();
    expect(screen.getByText(/неразрушающий/)).toBeInTheDocument();
    expect(screen.getByText(copy.searches_tender_pro_docs)).toBeInTheDocument();
    expect(screen.getByText(copy.session_tender_pro)).toBeInTheDocument();
    expect(screen.queryByText(/пока не подключён/)).not.toBeInTheDocument();
  });

  it("toggles in_queue from the switch", async () => {
    const user = userEvent.setup();
    const { onToggleQueue } = renderPanel(idle);
    await user.click(screen.getByLabelText(`${copy.searches_queue}: ${tenderPro.name}`));
    expect(onToggleQueue).toHaveBeenCalledWith(tenderPro, true);
  });
});

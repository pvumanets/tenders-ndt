import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";
import type { TechStatus } from "../../types";
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
  log: [],
};

function renderPanel(status: TechStatus, extra?: Partial<Parameters<typeof TechRunPanel>[0]>) {
  const onStart = extra?.onStart ?? vi.fn();
  const onStop = extra?.onStop ?? vi.fn();
  render(
    <ThemeRegistry>
      <TechRunPanel
        status={status}
        busy={extra?.busy}
        error={extra?.error}
        onStart={onStart}
        onStop={onStop}
      />
    </ThemeRegistry>,
  );
  return { onStart, onStop };
}

describe("TechRunPanel", () => {
  it("enables start when idle with cookies", async () => {
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

  it("disables start without cookies", () => {
    renderPanel({ ...idle, session: "missing" });
    expect(screen.getByRole("button", { name: copy.run_start })).toBeDisabled();
    expect(screen.getByRole("button", { name: copy.run_stop })).toBeDisabled();
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
});

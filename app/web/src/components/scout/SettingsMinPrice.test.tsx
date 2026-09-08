import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import SettingsMinPrice from "./SettingsMinPrice";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";
import * as inbox from "../../lib/inbox";
import type { OperatorSettings } from "../../types";

const baseSettings: OperatorSettings = {
  l1_min_price_rub: 100_000,
  ai_system_prompt: "p",
  ai_system_prompt_is_default: true,
};

describe("SettingsMinPrice", () => {
  it("saves snapped min price", async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    const putSpy = vi.spyOn(inbox, "putOperatorSettings").mockResolvedValue({
      ...baseSettings,
      l1_min_price_rub: 120_000,
    });

    render(
      <ThemeRegistry>
        <SettingsMinPrice settings={baseSettings} locked={false} onSaved={onSaved} />
      </ThemeRegistry>,
    );

    await user.click(screen.getByRole("button", { name: copy.min_price_save }));
    await waitFor(() => {
      expect(putSpy).toHaveBeenCalledWith({ l1_min_price_rub: 100_000 });
      expect(onSaved).toHaveBeenCalledWith({
        ...baseSettings,
        l1_min_price_rub: 120_000,
      });
    });
    putSpy.mockRestore();
  });

  it("updates threshold label when slider moves", () => {
    render(
      <ThemeRegistry>
        <SettingsMinPrice settings={baseSettings} locked={false} onSaved={vi.fn()} />
      </ThemeRegistry>,
    );

    const slider = screen.getAllByRole("slider")[0];
    fireEvent.change(slider, { target: { value: "250000" } });
    expect(slider).toHaveAttribute("aria-valuenow", "250000");
  });
});

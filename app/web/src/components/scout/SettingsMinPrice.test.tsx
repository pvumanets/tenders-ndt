import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import SettingsMinPrice from "./SettingsMinPrice";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";
import * as inbox from "../../lib/inbox";

describe("SettingsMinPrice", () => {
  it("saves snapped min price", async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    const putSpy = vi.spyOn(inbox, "putOperatorSettings").mockResolvedValue({ l1_min_price_rub: 120_000 });

    render(
      <ThemeRegistry>
        <SettingsMinPrice
          settings={{ l1_min_price_rub: 100_000 }}
          locked={false}
          onSaved={onSaved}
        />
      </ThemeRegistry>,
    );

    await user.click(screen.getByRole("button", { name: copy.min_price_save }));
    await waitFor(() => {
      expect(putSpy).toHaveBeenCalledWith({ l1_min_price_rub: 100_000 });
      expect(onSaved).toHaveBeenCalledWith({ l1_min_price_rub: 120_000 });
    });
    putSpy.mockRestore();
  });
});

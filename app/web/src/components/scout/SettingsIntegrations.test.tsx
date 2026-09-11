import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";
import type { OperatorSettings } from "../../types";
import * as inbox from "../../lib/inbox";
import SettingsProvodKey from "./SettingsProvodKey";
import SettingsBitrix from "./SettingsBitrix";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const baseSettings: OperatorSettings = {
  l1_min_price_rub: 100_000,
  ai_system_prompt: "p",
  ai_system_prompt_is_default: true,
  provod_api_key: { configured: true, hint: "••••ab12" },
  bitrix_webhook_url: { configured: true, hint: "••••rest" },
  bitrix_assigned_by_id: "71",
  bitrix_lead_source_id: "TENDERS_UMANETS",
  bitrix_chat_dialog_id: "chat7543",
  bitrix_ops_dialog_id: "951",
  bitrix_send_chat: true,
  bitrix_auto_l1_enabled: true,
  bitrix_ops_alerts_enabled: true,
};

describe("Settings integrations", () => {
  it("saves provod key and clears input", async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    const putSpy = vi.spyOn(inbox, "putOperatorSettings").mockResolvedValue({
      ...baseSettings,
      provod_api_key: { configured: true, hint: "••••zz99" },
    });

    render(
      <ThemeRegistry>
        <SettingsProvodKey settings={baseSettings} locked={false} onSaved={onSaved} />
      </ThemeRegistry>,
    );

    expect(screen.getByText(/••••ab12/)).toBeInTheDocument();
    await user.type(screen.getByLabelText(copy.integrations_provod_label), "new_secret_key_zz99");
    await user.click(screen.getByRole("button", { name: copy.integrations_save }));
    await waitFor(() => {
      expect(putSpy).toHaveBeenCalledWith({ provod_api_key: "new_secret_key_zz99" });
      expect(onSaved).toHaveBeenCalled();
    });
  });

  it("saves bitrix toggles and ids", async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    const putSpy = vi.spyOn(inbox, "putOperatorSettings").mockResolvedValue({
      ...baseSettings,
      bitrix_auto_l1_enabled: false,
      bitrix_send_chat: false,
    });

    render(
      <ThemeRegistry>
        <SettingsBitrix settings={baseSettings} locked={false} onSaved={onSaved} />
      </ThemeRegistry>,
    );

    await user.click(screen.getByLabelText(copy.integrations_auto_l1));
    await user.click(screen.getByLabelText(copy.integrations_send_chat));
    await user.click(screen.getByRole("button", { name: copy.integrations_save }));
    await waitFor(() => {
      expect(putSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          bitrix_auto_l1_enabled: false,
          bitrix_send_chat: false,
          bitrix_chat_dialog_id: "chat7543",
          bitrix_ops_dialog_id: "951",
        }),
      );
      expect(onSaved).toHaveBeenCalled();
    });
  });

  it("resets bitrix block to env", async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    const putSpy = vi.spyOn(inbox, "putOperatorSettings").mockResolvedValue({
      ...baseSettings,
      bitrix_webhook_url: { configured: false, hint: "" },
      bitrix_assigned_by_id: "",
      bitrix_chat_dialog_id: "",
    });

    render(
      <ThemeRegistry>
        <SettingsBitrix settings={baseSettings} locked={false} onSaved={onSaved} />
      </ThemeRegistry>,
    );

    await user.click(screen.getByRole("button", { name: copy.integrations_reset_env }));
    await waitFor(() => {
      expect(putSpy).toHaveBeenCalledWith({
        bitrix_webhook_url: null,
        bitrix_assigned_by_id: null,
        bitrix_lead_source_id: null,
        bitrix_chat_dialog_id: null,
        bitrix_ops_dialog_id: null,
        bitrix_send_chat: null,
        bitrix_auto_l1_enabled: null,
        bitrix_ops_alerts_enabled: null,
      });
      expect(onSaved).toHaveBeenCalled();
    });
  });
});

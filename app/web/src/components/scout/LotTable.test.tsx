import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { InboxLot } from "../../types";
import ThemeRegistry from "../../theme/ThemeRegistry";
import LotTable from "./LotTable";

afterEach(() => {
  cleanup();
});

const lot: InboxLot = {
  tender_id: "rostender:r4-1",
  title: "УЗК труб R4",
  customer_name: "ООО Тест",
  score: 8,
  tier: "L1",
  manual_tier: null,
  viewed: false,
  board_hidden: false,
  deadline_expired: false,
  deadline_msk: "01.01.2027",
  published_msk: "",
  ingested_at: "2026-09-07",
  price_rub: 1_000_000,
  location: "Челябинск",
  status: "Прием",
  fit_reason: "НК",
  contact_name: null,
  contact_phone: null,
  contact_email: null,
  url: "https://example.test/1",
  source_platform_id: "rostender",
  documents: [],
  docs_status: "missing" as const,
  docs_external_url: null,
  rules_tier: "L1",
  ai_reviewed: false,
  ai_tier: null,
  ai_reason_ru: "",
  ai_error: null,
  ai_wrong: false,
  ai_wrong_note: null,
  ai_trigger: null,
  bitrix_sent_at: null,
  customer_inn: null,
};

describe("LotTable keyboard", () => {
  it("opens lot on Enter and Space", async () => {
    const onOpen = vi.fn();
    const user = userEvent.setup();
    render(
      <ThemeRegistry>
        <LotTable lots={[lot]} selectedId={null} onOpen={onOpen} boardTier={(row) => row.tier} />
      </ThemeRegistry>,
    );
    const row = screen.getByRole("button", { name: lot.title });
    row.focus();
    await user.keyboard("{Enter}");
    await user.keyboard(" ");
    expect(onOpen).toHaveBeenCalledWith(lot.tender_id);
    expect(onOpen).toHaveBeenCalledTimes(2);
  });

  it("sortable headers call onSort for three modes only", async () => {
    const onSort = vi.fn();
    const user = userEvent.setup();
    render(
      <ThemeRegistry>
        <LotTable
          lots={[lot]}
          selectedId={null}
          onOpen={() => {}}
          boardTier={(row) => row.tier}
          sort="relevance"
          onSort={onSort}
        />
      </ThemeRegistry>,
    );
    await user.click(screen.getByRole("button", { name: /Попало к нам/i }));
    expect(onSort).toHaveBeenCalledWith("appeared");
    await user.click(screen.getByRole("button", { name: /^Срок$/i }));
    expect(onSort).toHaveBeenCalledWith("deadline");
    await user.click(screen.getByRole("button", { name: /Приоритет/i }));
    expect(onSort).toHaveBeenCalledWith("relevance");
  });
});

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { InboxLot } from "../../types";
import { copy } from "../../copy";
import ThemeRegistry from "../../theme/ThemeRegistry";
import LotMiniCard from "./LotMiniCard";

afterEach(() => {
  cleanup();
});

function baseLot(partial: Partial<InboxLot> = {}): InboxLot {
  return {
    tender_id: "t1",
    title: "УЗК",
    customer_name: "ООО",
    score: 7,
    tier: "L1",
    manual_tier: null,
    viewed: false,
    board_hidden: false,
    deadline_expired: true,
    deadline_msk: "2026-08-01",
    published_msk: "",
    ingested_at: "2026-09-01",
    price_rub: 1000,
    location: "Казань",
    status: "",
    fit_reason: "",
    contact_name: null,
    contact_phone: null,
    contact_email: null,
    url: "",
    source_platform_id: "rostender",
    documents: [],
    docs_status: "missing" as const,
    docs_external_url: null,
    rules_tier: "L3",
    ai_reviewed: true,
    ai_tier: "L1",
    ai_reason_ru: "",
    ai_error: null,
    ai_wrong: false,
    ai_trigger: "manual",
    bitrix_sent_at: null,
    customer_inn: null,
    ...partial,
  };
}

describe("LotMiniCard badges and dates", () => {
  it("spaces stacked chips and shows ingested date", () => {
    const { container } = render(
      <ThemeRegistry>
        <LotMiniCard lot={baseLot()} onOpen={() => {}} showTierMove />
      </ThemeRegistry>,
    );
    expect(screen.getByText("L3 → L1")).toBeInTheDocument();
    expect(screen.getByText(copy.badge_deadline_expired)).toBeInTheDocument();
    expect(screen.getByText(copy.col_ingested)).toBeInTheDocument();
    expect(screen.getByText("01.09.2026")).toBeInTheDocument();
    const badgeStack = container.querySelector(".MuiStack-root");
    expect(badgeStack).toBeTruthy();
  });
});

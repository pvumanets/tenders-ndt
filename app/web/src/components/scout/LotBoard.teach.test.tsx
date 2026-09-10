import { describe, expect, it, vi } from "vitest";
import { boardBucket } from "./LotBoard";
import { createBoardDropHandlers, createDragStartHandler, DRAG_MIME } from "../../lib/board-dnd";
import type { InboxLot } from "../../types";
import type { DragEvent } from "react";

function lot(partial: Partial<InboxLot>): InboxLot {
  return {
    tender_id: "t1",
    title: "x",
    customer_name: "",
    score: 1,
    tier: "L2",
    effective_tier: "L2",
    manual_tier: null,
    viewed: false,
    board_hidden: false,
    deadline_expired: false,
    deadline_msk: "10.10.2026",
    published_msk: "",
    ingested_at: "2026-09-01T00:00:00Z",
    price_rub: null,
    location: "",
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
    rules_tier: "L2",
    ai_reviewed: false,
    ai_tier: null,
    ai_reason_ru: "",
    ai_error: null,
    ai_wrong: false,
    ai_trigger: null,
    bitrix_sent_at: null,
    customer_inn: null,
    ...partial,
  };
}

describe("boardBucket", () => {
  it("returns expired when deadline_expired", () => {
    expect(boardBucket(lot({ deadline_expired: true, tier: "L1" }), () => "L1")).toBe("expired");
  });

  it("returns live tier otherwise", () => {
    expect(boardBucket(lot({ deadline_expired: false }), (l) => l.tier)).toBe("L2");
  });
});

describe("board-dnd HTML5 handlers", () => {
  it("sets MIME on drag start", () => {
    const setData = vi.fn();
    const handler = createDragStartHandler("rostender:1");
    handler({
      dataTransfer: { setData, effectAllowed: "none" },
    } as unknown as DragEvent);
    expect(setData).toHaveBeenCalledWith(DRAG_MIME, "rostender:1");
  });

  it("reads MIME on drop", () => {
    const onDropLot = vi.fn();
    const { onDrop, onDragOver } = createBoardDropHandlers("L3", onDropLot);
    const preventDefault = vi.fn();
    onDragOver({
      preventDefault,
      dataTransfer: { dropEffect: "none" },
    } as unknown as DragEvent);
    expect(preventDefault).toHaveBeenCalled();
    onDrop({
      preventDefault,
      dataTransfer: { getData: () => "rostender:9" },
    } as unknown as DragEvent);
    expect(onDropLot).toHaveBeenCalledWith("rostender:9", "L3");
  });
});

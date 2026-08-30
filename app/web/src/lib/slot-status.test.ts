import { describe, expect, it } from "vitest";
import type { ScheduleSettings, TechStatus } from "../types";
import { copy } from "../copy";
import { needsSessionBanner, slotVariant, slotStatusText } from "./slot-status";

const idleStatus: Pick<TechStatus, "pipeline" | "running" | "ai_review_done" | "ai_review_total"> = {
  pipeline: "manual",
  running: false,
  ai_review_done: 0,
  ai_review_total: 0,
};

const schedule: ScheduleSettings = {
  enabled: true,
  time_msk: "07:00",
  last_fired_at: null,
  last_skip_reason: null,
  last_attempt_at: null,
  next_fire_at: null,
};

describe("slotVariant", () => {
  it("is running when auto pipeline is in progress", () => {
    expect(
      slotVariant(schedule, { ...idleStatus, pipeline: "auto", running: true }),
    ).toBe("running");
  });

  it("shows skip already_running for today's attempt", () => {
    const now = new Date("2026-08-30T10:00:00+03:00");
    const row = {
      ...schedule,
      last_skip_reason: "already_running",
      last_attempt_at: "2026-08-30T07:00:00+03:00",
    };
    expect(slotVariant(row, idleStatus, now)).toBe("skipped_already_running");
    expect(slotStatusText(row, idleStatus, now)).toBe(copy.auto_slot_skipped_already_running);
  });

  it("falls back to idle with time_msk", () => {
    expect(slotStatusText(schedule, idleStatus)).toBe(
      copy.auto_slot_idle.replace("{time}", "07:00"),
    );
  });
});

describe("needsSessionBanner", () => {
  it("ignores Tender.Pro list_without_login", () => {
    expect(
      needsSessionBanner([
        { enabled: true, session: "list_without_login" },
        { enabled: true, session: "ok" },
      ]),
    ).toBe(false);
  });

  it("shows when an enabled platform is expired", () => {
    expect(
      needsSessionBanner([
        { enabled: true, session: "expired" },
        { enabled: true, session: "list_without_login" },
      ]),
    ).toBe(true);
  });
});

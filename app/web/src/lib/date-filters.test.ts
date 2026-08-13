import { describe, expect, it } from "vitest";
import { addDaysIso, deadlineQuery, ingestedQuery } from "./date-filters";

describe("deadlineQuery", () => {
  const today = "2026-08-13";

  it("omits params for any", () => {
    expect(deadlineQuery("any", "2026-08-01", "2026-08-20", today)).toEqual({});
  });

  it("maps d7 to today..today+7", () => {
    expect(deadlineQuery("d7", "", "", today)).toEqual({
      deadline_from: today,
      deadline_to: addDaysIso(today, 7),
    });
  });

  it("maps custom from/to", () => {
    expect(deadlineQuery("custom", "2026-08-14", "2026-08-20", today)).toEqual({
      deadline_from: "2026-08-14",
      deadline_to: "2026-08-20",
    });
  });
});

describe("ingestedQuery", () => {
  const today = "2026-08-13";

  it("omits params for any", () => {
    expect(ingestedQuery("any", "", "", today)).toEqual({});
  });

  it("maps today to a single-day range", () => {
    expect(ingestedQuery("today", "", "", today)).toEqual({
      ingested_from: today,
      ingested_to: today,
    });
  });

  it("maps d3 inclusive of today-2", () => {
    expect(ingestedQuery("d3", "", "", today)).toEqual({
      ingested_from: addDaysIso(today, -2),
      ingested_to: today,
    });
  });
});

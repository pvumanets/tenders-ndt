import type { DeadlinePreset, IngestedPreset } from "../types";

/** Calendar date YYYY-MM-DD in Europe/Moscow. */
export function mskTodayIso(now = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Moscow",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(now);
}

export function datePart(value: string): string {
  return value.slice(0, 10);
}

export function addDaysIso(iso: string, days: number): string {
  const [y, m, d] = datePart(iso).split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  dt.setUTCDate(dt.getUTCDate() + days);
  return dt.toISOString().slice(0, 10);
}

export function inDateRange(value: string, from: string, to: string): boolean {
  const d = datePart(value);
  if (from && d < from) return false;
  if (to && d > to) return false;
  return true;
}

/** `deadline_msk` ∈ [today .. today+N] (MSK). Custom = optional from–to. */
export function matchesDeadline(
  deadlineMsk: string,
  preset: DeadlinePreset,
  from: string,
  to: string,
  today: string,
): boolean {
  const d = datePart(deadlineMsk);
  if (preset === "any") return true;
  if (preset === "custom") return inDateRange(d, from, to);
  const n = preset === "d7" ? 7 : preset === "d14" ? 14 : 30;
  return d >= today && d <= addDaysIso(today, n);
}

/** `ingested_at` ≥ today−(N−1), inclusive. «Сегодня» = N=1. */
export function matchesIngested(
  ingestedAt: string,
  preset: IngestedPreset,
  from: string,
  to: string,
  today: string,
): boolean {
  const d = datePart(ingestedAt);
  if (preset === "any") return true;
  if (preset === "custom") return inDateRange(d, from, to);
  const n = preset === "today" ? 1 : preset === "d3" ? 3 : 7;
  return d >= addDaysIso(today, -(n - 1)) && d <= today;
}

export function deadlineQuery(
  preset: DeadlinePreset,
  from: string,
  to: string,
  today: string,
): { deadline_from?: string; deadline_to?: string } {
  if (preset === "any") return {};
  if (preset === "custom") {
    const query: { deadline_from?: string; deadline_to?: string } = {};
    if (from) query.deadline_from = from;
    if (to) query.deadline_to = to;
    return query;
  }
  const n = preset === "d7" ? 7 : preset === "d14" ? 14 : 30;
  return { deadline_from: today, deadline_to: addDaysIso(today, n) };
}

export function ingestedQuery(
  preset: IngestedPreset,
  from: string,
  to: string,
  today: string,
): { ingested_from?: string; ingested_to?: string } {
  if (preset === "any") return {};
  if (preset === "custom") {
    const query: { ingested_from?: string; ingested_to?: string } = {};
    if (from) query.ingested_from = from;
    if (to) query.ingested_to = to;
    return query;
  }
  const n = preset === "today" ? 1 : preset === "d3" ? 3 : 7;
  return { ingested_from: addDaysIso(today, -(n - 1)), ingested_to: today };
}

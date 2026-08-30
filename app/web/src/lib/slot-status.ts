import type { ScheduleSettings, TechStatus } from "../types";
import { copy } from "../copy";
import { mskTodayIso } from "./date-filters";

export type SlotVariant = "running" | "skipped_already_running" | "skipped_empty_queue" | "last" | "idle";

export function mskDateOfIso(stamp: string | null | undefined): string | null {
  if (!stamp) return null;
  const parsed = new Date(stamp);
  if (Number.isNaN(parsed.getTime())) return null;
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Moscow",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(parsed);
}

function isTodayMsk(stamp: string | null | undefined, now = new Date()): boolean {
  const day = mskDateOfIso(stamp);
  return day != null && day === mskTodayIso(now);
}

export function formatMskDateTime(stamp: string): string {
  const parsed = new Date(stamp);
  if (Number.isNaN(parsed.getTime())) return stamp;
  return new Intl.DateTimeFormat("ru-RU", {
    timeZone: "Europe/Moscow",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

export function isAutoAiInProgress(status: Pick<TechStatus, "pipeline" | "running" | "ai_review_done" | "ai_review_total">): boolean {
  if (status.pipeline === "auto" && status.running) return true;
  return status.pipeline === "auto" && status.ai_review_total > 0 && status.ai_review_done < status.ai_review_total;
}

export function slotVariant(
  schedule: ScheduleSettings,
  status: Pick<TechStatus, "pipeline" | "running" | "ai_review_done" | "ai_review_total">,
  now = new Date(),
): SlotVariant {
  if (isAutoAiInProgress(status)) return "running";
  if (isTodayMsk(schedule.last_attempt_at, now) && schedule.last_skip_reason === "already_running") {
    return "skipped_already_running";
  }
  if (isTodayMsk(schedule.last_attempt_at, now) && schedule.last_skip_reason === "empty_queue") {
    return "skipped_empty_queue";
  }
  if (isTodayMsk(schedule.last_fired_at, now) && !status.running) return "last";
  return "idle";
}

export function needsSessionBanner(platforms: { enabled: boolean; session: string }[]): boolean {
  return platforms.some(
    (row) => row.enabled && (row.session === "expired" || row.session === "missing"),
  );
}

export function slotStatusText(
  schedule: ScheduleSettings,
  status: Pick<TechStatus, "pipeline" | "running" | "ai_review_done" | "ai_review_total">,
  now = new Date(),
): string {
  const variant = slotVariant(schedule, status, now);
  if (variant === "running") return copy.auto_slot_running;
  if (variant === "skipped_already_running") return copy.auto_slot_skipped_already_running;
  if (variant === "skipped_empty_queue") return copy.auto_slot_skipped_empty_queue;
  if (variant === "last" && schedule.last_fired_at) {
    return copy.auto_slot_last.replace("{datetime}", formatMskDateTime(schedule.last_fired_at));
  }
  return copy.auto_slot_idle.replace("{time}", schedule.time_msk);
}

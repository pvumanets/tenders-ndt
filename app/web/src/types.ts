export type SalesTier = "L1" | "L2" | "L3";
export type ViewMode = "cards" | "table";
export type AppTab = "auto" | "manual" | "settings";
export type AiTrigger = "auto" | "manual";
export type RunPipeline = "manual" | "auto";

export type DocFile = {
  name: string;
  size_kb?: number;
};

export type InboxLot = {
  tender_id: string;
  title: string;
  customer_name: string;
  score: number;
  tier: SalesTier;
  manual_tier: SalesTier | null;
  viewed: boolean;
  board_hidden: boolean;
  deadline_expired: boolean;
  deadline_msk: string;
  ingested_at: string;
  price_rub: number | null;
  location: string;
  status: string;
  fit_reason: string;
  contact_name: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  url: string;
  /** slug из docs/discovery/platforms.md */
  source_platform_id: string;
  documents: DocFile[];
  rules_tier: SalesTier | null;
  ai_reviewed: boolean;
  ai_tier: SalesTier | null;
  ai_reason_ru: string;
  ai_error: string | null;
  ai_wrong: boolean;
  ai_trigger: AiTrigger | null;
};

export type SearchGroup = {
  id: string;
  name: string;
  queries: string[];
  exclude: string[];
  limit_n: number;
  in_queue: boolean;
  sort_order: number;
};

export type PlatformSession =
  | "ok"
  | "missing"
  | "expired"
  | "list_without_login"
  | "unknown";

export type PlatformRow = {
  platform_id: string;
  name: string;
  enabled: boolean;
  session: PlatformSession;
};

export type QueueStepStatus = "pending" | "running" | "done" | "skipped" | "error" | "cancelled";

export type QueueStep = {
  id: string;
  name: string;
  group_id?: string;
  group_name?: string;
  platform_id: string;
  status: QueueStepStatus;
};

export type ScheduleSettings = {
  enabled: boolean;
  time_msk: string;
  last_fired_at: string | null;
  last_skip_reason: string | null;
  last_attempt_at: string | null;
  next_fire_at: string | null;
};

export type TechStatus = {
  phase: string;
  phase_label: string;
  running: boolean;
  pipeline: RunPipeline;
  list_done: number;
  list_total: number;
  cards_done: number;
  cards_total: number;
  counters: { L1: number; L2: number; L3: number; noise: number };
  run_report: { new: number; already: number; updated: number; expired: number };
  ai_failures: number;
  ai_review_done: number;
  ai_review_total: number;
  http_retries: number;
  session: "ok" | "expired" | "missing";
  sessions?: { rostender?: string; "tender-pro"?: string; roseltorg?: string };
  run_dir: string;
  queue: QueueStep[];
  queue_index: number;
  queue_total: number;
  current_search_name: string;
  current_group_id?: string;
  current_platform_id?: string;
  log: { t: string; msg: string; level?: "error" | "info" }[];
};

/** Empty = no priority filter (all tiers). Otherwise match any selected. */
export type PriorityFilter = SalesTier[];

/** Срок подачи: Любой / ≤7 / ≤14 / ≤30 / Свой период */
export type DeadlinePreset = "any" | "d7" | "d14" | "d30" | "custom";

/** Попало к нам: Любое / Сегодня / 3д / 7д / Свой период */
export type IngestedPreset = "any" | "today" | "d3" | "d7" | "custom";

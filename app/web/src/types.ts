export type SalesTier = "L1" | "L2" | "L3";
export type ViewMode = "cards" | "table";
export type AppTab = "lots" | "run";

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
};

export type TechStatus = {
  phase: string;
  phase_label: string;
  running: boolean;
  list_done: number;
  list_total: number;
  cards_done: number;
  cards_total: number;
  counters: { L1: number; L2: number; L3: number; noise: number };
  session: "ok" | "expired" | "missing";
  run_dir: string;
  log: { t: string; msg: string; level?: "error" | "info" }[];
};

/** Empty = no priority filter (all tiers). Otherwise match any selected. */
export type PriorityFilter = SalesTier[];

/** Срок подачи: Любой / ≤7 / ≤14 / ≤30 / Свой период */
export type DeadlinePreset = "any" | "d7" | "d14" | "d30" | "custom";

/** Попало к нам: Любое / Сегодня / 3д / 7д / Свой период */
export type IngestedPreset = "any" | "today" | "d3" | "d7" | "custom";

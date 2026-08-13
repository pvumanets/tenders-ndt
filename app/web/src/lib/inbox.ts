import type { InboxLot, PriorityFilter, SalesTier, TechStatus } from "../types";
import { copy } from "../copy";

export class UnauthorizedError extends Error {
  constructor() {
    super("unauthorized");
    this.name = "UnauthorizedError";
  }
}

export type InboxListQuery = {
  unread?: boolean;
  tier?: "fit" | SalesTier;
  q?: string;
  deadline_from?: string;
  deadline_to?: string;
  ingested_from?: string;
  ingested_to?: string;
};

type ApiLot = Partial<InboxLot> & {
  tender_id?: string;
  title?: string;
  score?: number;
  tier?: SalesTier;
  documents?: InboxLot["documents"] | null;
};

type StatusSnapshot = {
  phase?: string;
  running?: boolean;
  list_n?: number;
  list_limit?: number;
  cards_done?: number;
  cards_total?: number;
  counters?: Partial<TechStatus["counters"]> & { pool?: number };
  session?: string;
  run_dir?: string | null;
  log?: TechStatus["log"];
};

async function apiFetch(url: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(url, { credentials: "include", ...init });
  if (res.status === 401) throw new UnauthorizedError();
  return res;
}

function text(value: unknown): string {
  if (value == null) return "";
  return String(value);
}

export function normalizeLot(raw: ApiLot): InboxLot {
  const tier = raw.tier === "L2" || raw.tier === "L3" ? raw.tier : "L1";
  const manual =
    raw.manual_tier === "L1" || raw.manual_tier === "L2" || raw.manual_tier === "L3"
      ? raw.manual_tier
      : null;
  return {
    tender_id: text(raw.tender_id),
    title: text(raw.title),
    customer_name: text(raw.customer_name),
    score: typeof raw.score === "number" ? raw.score : 0,
    tier,
    manual_tier: manual,
    viewed: Boolean(raw.viewed),
    deadline_msk: text(raw.deadline_msk),
    ingested_at: text(raw.ingested_at),
    price_rub: typeof raw.price_rub === "number" ? raw.price_rub : null,
    location: text(raw.location),
    status: text(raw.status),
    fit_reason: text(raw.fit_reason),
    contact_name: raw.contact_name ?? null,
    contact_phone: raw.contact_phone ?? null,
    contact_email: raw.contact_email ?? null,
    url: text(raw.url),
    source_platform_id: text(raw.source_platform_id) || "rostender",
    documents: Array.isArray(raw.documents) ? raw.documents : [],
  };
}

export function apiTierParam(priority: PriorityFilter): "fit" | SalesTier {
  return priority.length === 1 ? priority[0] : "fit";
}

export function buildInboxSearchParams(query: InboxListQuery): URLSearchParams {
  const params = new URLSearchParams();
  if (query.unread) params.set("unread", "true");
  params.set("tier", query.tier ?? "fit");
  if (query.q) params.set("q", query.q);
  if (query.deadline_from) params.set("deadline_from", query.deadline_from);
  if (query.deadline_to) params.set("deadline_to", query.deadline_to);
  if (query.ingested_from) params.set("ingested_from", query.ingested_from);
  if (query.ingested_to) params.set("ingested_to", query.ingested_to);
  return params;
}

export function documentDownloadUrl(tenderId: string, filename: string): string {
  return `/api/inbox/${encodeURIComponent(tenderId)}/documents/${encodeURIComponent(filename)}`;
}

export async function fetchInbox(query: InboxListQuery): Promise<InboxLot[]> {
  const res = await apiFetch(`/api/inbox?${buildInboxSearchParams(query).toString()}`);
  if (!res.ok) throw new Error("inbox_load_failed");
  const body = (await res.json()) as { items?: ApiLot[] };
  return Array.isArray(body.items) ? body.items.map(normalizeLot) : [];
}

export async function fetchInboxItem(tenderId: string): Promise<InboxLot> {
  const res = await apiFetch(`/api/inbox/${encodeURIComponent(tenderId)}`);
  if (res.status === 404) throw new Error("not_found");
  if (!res.ok) throw new Error("inbox_load_failed");
  return normalizeLot((await res.json()) as ApiLot);
}

export async function putViewed(tenderId: string, viewed: boolean): Promise<InboxLot> {
  const res = await apiFetch(`/api/inbox/${encodeURIComponent(tenderId)}/viewed`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ viewed }),
  });
  if (!res.ok) throw new Error("inbox_write_failed");
  return normalizeLot((await res.json()) as ApiLot);
}

export async function putPriority(tenderId: string, tier: SalesTier | null): Promise<InboxLot> {
  const res = await apiFetch(`/api/inbox/${encodeURIComponent(tenderId)}/priority`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tier }),
  });
  if (!res.ok) throw new Error("inbox_write_failed");
  return normalizeLot((await res.json()) as ApiLot);
}

function phaseLabel(phase: string): string {
  switch (phase) {
    case "P1":
      return copy.phase_list;
    case "P2":
      return copy.phase_score;
    case "P3":
      return copy.phase_cards;
    case "P4":
      return copy.phase_artifacts;
    case "done":
      return copy.phase_done;
    case "stopped":
      return copy.phase_stopped;
    case "error":
      return copy.phase_error;
    default:
      return copy.phase_idle;
  }
}

function sessionUi(raw: string | undefined): TechStatus["session"] {
  if (raw === "ok") return "ok";
  if (raw === "expired") return "expired";
  return "missing";
}

export function mapRunStatus(raw: StatusSnapshot): TechStatus {
  return {
    phase: raw.phase ?? "idle",
    phase_label: phaseLabel(raw.phase ?? "idle"),
    running: Boolean(raw.running),
    list_done: raw.list_n ?? 0,
    list_total: raw.list_limit ?? 0,
    cards_done: raw.cards_done ?? 0,
    cards_total: raw.cards_total ?? 0,
    counters: {
      L1: raw.counters?.L1 ?? 0,
      L2: raw.counters?.L2 ?? 0,
      L3: raw.counters?.L3 ?? 0,
      noise: raw.counters?.noise ?? 0,
    },
    session: sessionUi(raw.session),
    run_dir: raw.run_dir ?? "",
    log: Array.isArray(raw.log) ? raw.log : [],
  };
}

export async function fetchStatus(): Promise<TechStatus> {
  const res = await apiFetch("/api/status");
  if (!res.ok) throw new Error("status_load_failed");
  return mapRunStatus((await res.json()) as StatusSnapshot);
}

import type {
  AiTrigger,
  BitrixFilter,
  InboxLot,
  PlatformRow,
  PlatformSession,
  PriorityFilter,
  QueueStep,
  QueueStepStatus,
  SalesTier,
  ScheduleSettings,
  SearchGroup,
  TechStatus,
  OperatorSettings,
  InboxSort,
  TeachBucket,
} from "../types";
import { copy } from "../copy";

export class UnauthorizedError extends Error {
  constructor() {
    super("unauthorized");
    this.name = "UnauthorizedError";
  }
}

export class BitrixSendError extends Error {
  readonly code: string;

  constructor(code: string) {
    super(code);
    this.name = "BitrixSendError";
    this.code = code;
  }
}

export type RunControlCode = "already_running" | "missing_cookies" | "empty_queue" | "failed";

export class RunControlError extends Error {
  readonly code: RunControlCode;

  constructor(code: RunControlCode) {
    super(code);
    this.name = "RunControlError";
    this.code = code;
  }
}

export function runControlMessage(code: RunControlCode): string {
  if (code === "already_running") return copy.run_error_already;
  if (code === "missing_cookies") return copy.run_error_cookies;
  if (code === "empty_queue") return copy.run_error_empty_queue;
  return copy.run_error_failed;
}

export type InboxListQuery = {
  unread?: boolean;
  tier?: "fit" | SalesTier;
  q?: string;
  deadline_from?: string;
  deadline_to?: string;
  ingested_from?: string;
  ingested_to?: string;
  ai_reviewed?: boolean;
  ai_trigger?: AiTrigger;
  ai_wrong?: boolean;
  price_min_rub?: number;
  platform?: string;
  bitrix?: Exclude<BitrixFilter, "any">;
  sort?: InboxSort;
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
  run_report?: Partial<TechStatus["run_report"]>;
  ai_failures?: number;
  http_retries?: number;
  session?: string;
  sessions?: Record<string, string>;
  run_dir?: string | null;
  log?: TechStatus["log"];
  queue?: Array<Partial<QueueStep> & { group_id?: string; group_name?: string }>;
  queue_index?: number;
  queue_total?: number;
  current_search_name?: string | null;
  current_group_id?: string | null;
  current_platform_id?: string | null;
  pipeline?: string;
  ai_review_done?: number;
  ai_review_total?: number;
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
  const aiTier =
    raw.ai_tier === "L1" || raw.ai_tier === "L2" || raw.ai_tier === "L3" ? raw.ai_tier : null;
  const effectiveTier =
    raw.effective_tier === "L1" || raw.effective_tier === "L2" || raw.effective_tier === "L3"
      ? raw.effective_tier
      : null;
  const rulesTier =
    raw.rules_tier === "L1" || raw.rules_tier === "L2" || raw.rules_tier === "L3"
      ? raw.rules_tier
      : null;
  return {
    tender_id: text(raw.tender_id),
    title: text(raw.title),
    customer_name: text(raw.customer_name),
    score: typeof raw.score === "number" ? raw.score : 0,
    tier,
    effective_tier: effectiveTier,
    manual_tier: manual,
    viewed: Boolean(raw.viewed),
    board_hidden: Boolean(raw.board_hidden),
    deadline_expired: Boolean(raw.deadline_expired),
    deadline_msk: text(raw.deadline_msk),
    published_msk: text(raw.published_msk),
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
    rules_tier: rulesTier,
    ai_reviewed: Boolean(raw.ai_reviewed),
    ai_tier: aiTier,
    ai_reason_ru: text(raw.ai_reason_ru),
    ai_error: raw.ai_error ? text(raw.ai_error) : null,
    ai_wrong: Boolean(raw.ai_wrong),
    ai_wrong_note: raw.ai_wrong_note ? text(raw.ai_wrong_note) : null,
    ai_trigger: raw.ai_trigger === "auto" || raw.ai_trigger === "manual" ? raw.ai_trigger : null,
    bitrix_sent_at: raw.bitrix_sent_at ? text(raw.bitrix_sent_at) : null,
    customer_inn: raw.customer_inn ? text(raw.customer_inn) : null,
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
  if (query.ai_reviewed === true) params.set("ai_reviewed", "1");
  if (query.ai_reviewed === false) params.set("ai_reviewed", "0");
  if (query.ai_trigger) params.set("ai_trigger", query.ai_trigger);
  if (query.ai_wrong === true) params.set("ai_wrong", "1");
  if (query.ai_wrong === false) params.set("ai_wrong", "0");
  if (query.price_min_rub != null && query.price_min_rub > 0) {
    params.set("price_min_rub", String(query.price_min_rub));
  }
  if (query.sort && query.sort !== "relevance") {
    params.set("sort", query.sort);
  }
  if (query.platform) params.set("platform", query.platform);
  if (query.bitrix) params.set("bitrix", query.bitrix);
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

export async function fetchInboxTotal(query: InboxListQuery): Promise<number> {
  const res = await apiFetch(`/api/inbox?${buildInboxSearchParams(query).toString()}`);
  if (!res.ok) throw new Error("inbox_load_failed");
  const body = (await res.json()) as { total?: unknown; items?: unknown[] };
  if (typeof body.total === "number") return body.total;
  return Array.isArray(body.items) ? body.items.length : 0;
}

export type InboxExportBody = InboxListQuery & {
  format: "csv" | "xlsx";
  columns: string[];
};

function filenameFromDisposition(header: string | null, fallback: string): string {
  if (!header) return fallback;
  const star = /filename\*=UTF-8''([^;]+)/i.exec(header);
  if (star?.[1]) {
    try {
      return decodeURIComponent(star[1].trim());
    } catch {
      /* keep fallback */
    }
  }
  const plain = /filename="([^"]+)"/i.exec(header) || /filename=([^;]+)/i.exec(header);
  if (plain?.[1]) return plain[1].trim();
  return fallback;
}

export async function postInboxExport(
  body: InboxExportBody,
): Promise<{ blob: Blob; filename: string }> {
  const payload: Record<string, unknown> = {
    format: body.format,
    columns: body.columns,
    tier: body.tier ?? "fit",
    q: body.q ?? "",
  };
  if (body.unread) payload.unread = true;
  if (body.deadline_from) payload.deadline_from = body.deadline_from;
  if (body.deadline_to) payload.deadline_to = body.deadline_to;
  if (body.ingested_from) payload.ingested_from = body.ingested_from;
  if (body.ingested_to) payload.ingested_to = body.ingested_to;
  if (body.ai_reviewed === true) payload.ai_reviewed = true;
  if (body.ai_reviewed === false) payload.ai_reviewed = false;
  if (body.ai_trigger) payload.ai_trigger = body.ai_trigger;
  if (body.ai_wrong === true) payload.ai_wrong = true;
  if (body.ai_wrong === false) payload.ai_wrong = false;
  if (body.price_min_rub != null && body.price_min_rub > 0) {
    payload.price_min_rub = body.price_min_rub;
  }
  if (body.platform) payload.platform = body.platform;
  if (body.bitrix) payload.bitrix = body.bitrix;
  if (body.sort && body.sort !== "relevance") payload.sort = body.sort;

  const res = await apiFetch("/api/inbox/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("export_failed");
  const blob = await res.blob();
  const filename = filenameFromDisposition(
    res.headers.get("Content-Disposition"),
    `inbox-export.${body.format}`,
  );
  return { blob, filename };
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

export type MarkAllViewedScope = {
  dry_run?: boolean;
  ai_reviewed?: boolean;
  ai_trigger?: "auto" | "manual";
};

export async function postMarkAllViewed(
  body: MarkAllViewedScope = {},
): Promise<{ count: number; updated: number }> {
  const res = await apiFetch("/api/inbox/mark-all-viewed", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("inbox_write_failed");
  const raw = (await res.json()) as { count?: unknown; updated?: unknown };
  return {
    count: typeof raw.count === "number" ? raw.count : 0,
    updated: typeof raw.updated === "number" ? raw.updated : 0,
  };
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

export async function postTierTeach(
  tenderId: string,
  body: {
    from_bucket: TeachBucket;
    to_bucket: TeachBucket;
    drop_tier_correct: boolean;
    reason_ru: string;
  },
): Promise<{ event_id: string; lot: InboxLot }> {
  const res = await apiFetch(`/api/inbox/${encodeURIComponent(tenderId)}/tier-teach`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("tier_teach_failed");
  const raw = (await res.json()) as { event_id?: string; lot?: ApiLot };
  if (!raw.lot || !raw.event_id) throw new Error("tier_teach_failed");
  return { event_id: raw.event_id, lot: normalizeLot(raw.lot) };
}

export async function putBoardHidden(tenderId: string, hidden: boolean): Promise<InboxLot> {
  const res = await apiFetch(`/api/inbox/${encodeURIComponent(tenderId)}/board-hidden`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ hidden }),
  });
  if (!res.ok) throw new Error("inbox_write_failed");
  return normalizeLot((await res.json()) as ApiLot);
}

export async function postAiReview(tenderIds?: string[]): Promise<{
  processed: number;
  failed: number;
  items: InboxLot[];
}> {
  const res = await apiFetch("/api/inbox/ai-review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(tenderIds ? { tender_ids: tenderIds } : {}),
  });
  if (!res.ok) throw new Error("ai_review_failed");
  const body = (await res.json()) as {
    processed?: number;
    failed?: number;
    items?: ApiLot[];
  };
  return {
    processed: body.processed ?? 0,
    failed: body.failed ?? 0,
    items: Array.isArray(body.items) ? body.items.map(normalizeLot) : [],
  };
}

export async function postAiWrong(tenderId: string, note?: string): Promise<InboxLot> {
  const res = await apiFetch(`/api/inbox/${encodeURIComponent(tenderId)}/ai-wrong`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(note ? { note } : {}),
  });
  if (!res.ok) throw new Error("ai_wrong_failed");
  return normalizeLot((await res.json()) as ApiLot);
}

export async function postBitrixSend(
  tenderId: string,
): Promise<{ lead_id: number | string; item: InboxLot }> {
  const res = await apiFetch(`/api/inbox/${encodeURIComponent(tenderId)}/bitrix`, {
    method: "POST",
  });
  if (res.status === 409) throw new BitrixSendError("already_sent");
  if (res.status === 400) {
    const body = (await res.json().catch(() => ({}))) as { detail?: unknown };
    const code = typeof body.detail === "string" ? body.detail : "bitrix_error";
    throw new BitrixSendError(code);
  }
  if (!res.ok) throw new BitrixSendError("bitrix_error");
  const raw = (await res.json()) as { lead_id?: unknown; item?: ApiLot };
  if (!raw.item) throw new BitrixSendError("bitrix_error");
  return {
    lead_id: typeof raw.lead_id === "number" || typeof raw.lead_id === "string" ? raw.lead_id : "",
    item: normalizeLot(raw.item),
  };
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
    case "partial":
      return copy.phase_partial;
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

const QUEUE_STATUSES: QueueStepStatus[] = [
  "pending",
  "running",
  "done",
  "skipped",
  "error",
  "cancelled",
];

function parseQueue(raw: StatusSnapshot["queue"]): QueueStep[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((item, index) => {
    const status = QUEUE_STATUSES.includes(item?.status as QueueStepStatus)
      ? (item.status as QueueStepStatus)
      : "pending";
    const groupName = text(item?.group_name) || text(item?.name);
    return {
      id: text(item?.id) || `step-${index}`,
      name: groupName,
      group_id: text(item?.group_id) || undefined,
      group_name: groupName || undefined,
      platform_id: text(item?.platform_id),
      status,
    };
  });
}

export function platformLabel(platformId: string): string {
  if (platformId === "tender-pro") return copy.platform_tender_pro;
  if (platformId === "rostender") return copy.platform_rostender;
  if (platformId === "roseltorg") return copy.platform_roseltorg;
  if (platformId === "b2b-center") return copy.platform_b2b_center;
  if (platformId === "rts-rosatom") return copy.platform_rts_rosatom;
  if (platformId === "oilb2bcs") return copy.platform_oilb2bcs;
  if (platformId === "sibur-srm") return copy.platform_sibur_srm;
  return platformId;
}

export function sessionStatusLabel(session: PlatformSession | string): string {
  switch (session) {
    case "ok":
      return copy.session_status_ok;
    case "missing":
      return copy.session_status_missing;
    case "expired":
      return copy.session_status_expired;
    case "blocked":
      return copy.session_status_blocked;
    case "list_without_login":
      return copy.session_status_list_without_login;
    default:
      return copy.session_status_unknown;
  }
}

export function formatPlatformSessionLine(platform: PlatformRow): string {
  return `${platform.name}: ${sessionStatusLabel(platform.session)}`;
}

export function queueStatusLabel(status: QueueStepStatus): string {
  switch (status) {
    case "running":
      return copy.queue_status_running;
    case "done":
      return copy.queue_status_done;
    case "skipped":
      return copy.queue_status_skipped;
    case "error":
      return copy.queue_status_error;
    case "cancelled":
      return copy.queue_status_cancelled;
    default:
      return copy.queue_status_pending;
  }
}

export function formatQueuePosition(current: number, total: number): string {
  return copy.queue_position
    .replace("{current}", String(current))
    .replace("{total}", String(total));
}

export function formatQueueSummary(groups: number, platforms: number, steps: number): string {
  return copy.run_queue_summary
    .replace("{groups}", String(groups))
    .replace("{platforms}", String(platforms))
    .replace("{steps}", String(steps));
}

export function formatQueueStepLine(
  current: number,
  total: number,
  group: string,
  platform: string,
): string {
  return copy.run_queue_step
    .replace("{current}", String(current))
    .replace("{total}", String(total))
    .replace("{group}", group)
    .replace("{platform}", platform);
}

export type SearchGroupWrite = {
  name: string;
  queries: string[];
  exclude: string[];
  limit_n: number;
  in_queue: boolean;
  sort_order: number;
};

export class SearchControlError extends Error {
  readonly code: "duplicate_name" | "failed";

  constructor(code: "duplicate_name" | "failed") {
    super(code);
    this.name = "SearchControlError";
    this.code = code;
  }
}

export function searchControlMessage(code: SearchControlError["code"]): string {
  if (code === "duplicate_name") return copy.groups_duplicate_name;
  return copy.groups_save_failed;
}

function parseSearchGroup(raw: Partial<SearchGroup>): SearchGroup {
  return {
    id: text(raw.id),
    name: text(raw.name),
    queries: Array.isArray(raw.queries) ? raw.queries.map((item) => text(item)).filter(Boolean) : [],
    exclude: Array.isArray(raw.exclude) ? raw.exclude.map((item) => text(item)).filter(Boolean) : [],
    limit_n: typeof raw.limit_n === "number" ? raw.limit_n : 0,
    in_queue: Boolean(raw.in_queue),
    sort_order: typeof raw.sort_order === "number" ? raw.sort_order : 0,
  };
}

function parsePlatformSession(raw: unknown): PlatformSession {
  if (raw === "ok") return "ok";
  if (raw === "missing") return "missing";
  if (raw === "expired") return "expired";
  if (raw === "blocked") return "blocked";
  if (raw === "list_without_login") return "list_without_login";
  return "unknown";
}

function parsePlatform(raw: Partial<PlatformRow> & { platform_id?: string }): PlatformRow {
  const platformId = text(raw.platform_id);
  return {
    platform_id: platformId,
    name: text(raw.name) || platformLabel(platformId),
    enabled: Boolean(raw.enabled),
    session: parsePlatformSession(raw.session),
  };
}

export async function fetchSearchGroups(): Promise<SearchGroup[]> {
  const res = await apiFetch("/api/search-groups");
  if (!res.ok) throw new Error("search_groups_load_failed");
  const body = (await res.json()) as { items?: Partial<SearchGroup>[] };
  return Array.isArray(body.items) ? body.items.map(parseSearchGroup) : [];
}

async function writeSearchGroup(res: Response): Promise<SearchGroup> {
  if (res.status === 409) throw new SearchControlError("duplicate_name");
  if (!res.ok) throw new SearchControlError("failed");
  return parseSearchGroup((await res.json()) as Partial<SearchGroup>);
}

export async function createSearchGroup(body: SearchGroupWrite): Promise<SearchGroup> {
  const res = await apiFetch("/api/search-groups", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return writeSearchGroup(res);
}

export async function updateSearchGroup(id: string, body: SearchGroupWrite): Promise<SearchGroup> {
  const res = await apiFetch(`/api/search-groups/${encodeURIComponent(id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return writeSearchGroup(res);
}

export async function deleteSearchGroup(id: string): Promise<void> {
  const res = await apiFetch(`/api/search-groups/${encodeURIComponent(id)}`, { method: "DELETE" });
  if (res.status === 404 || !res.ok) throw new SearchControlError("failed");
}

export async function fetchPlatforms(): Promise<PlatformRow[]> {
  const res = await apiFetch("/api/platforms");
  if (!res.ok) throw new Error("platforms_load_failed");
  const body = (await res.json()) as { items?: Array<Partial<PlatformRow>> };
  return Array.isArray(body.items) ? body.items.map(parsePlatform) : [];
}

export async function setPlatformEnabled(
  platformId: string,
  enabled: boolean,
): Promise<PlatformRow> {
  const res = await apiFetch(`/api/platforms/${encodeURIComponent(platformId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!res.ok) throw new SearchControlError("failed");
  return parsePlatform((await res.json()) as Partial<PlatformRow>);
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
    run_report: {
      new: raw.run_report?.new ?? 0,
      already: raw.run_report?.already ?? 0,
      updated: raw.run_report?.updated ?? 0,
      expired: raw.run_report?.expired ?? 0,
    },
    ai_failures: raw.ai_failures ?? 0,
    ai_review_done: raw.ai_review_done ?? 0,
    ai_review_total: raw.ai_review_total ?? 0,
    http_retries: raw.http_retries ?? 0,
    session: sessionUi(raw.session),
    sessions: raw.sessions,
    run_dir: raw.run_dir ?? "",
    queue: parseQueue(raw.queue),
    queue_index: raw.queue_index ?? 0,
    queue_total: raw.queue_total ?? (Array.isArray(raw.queue) ? raw.queue.length : 0),
    current_search_name: raw.current_search_name ?? "",
    current_group_id: raw.current_group_id ?? undefined,
    current_platform_id: raw.current_platform_id ?? undefined,
    pipeline: raw.pipeline === "auto" ? "auto" : "manual",
    log: Array.isArray(raw.log) ? raw.log : [],
  };
}

export async function fetchStatus(): Promise<TechStatus> {
  const res = await apiFetch("/api/status");
  if (!res.ok) throw new Error("status_load_failed");
  return mapRunStatus((await res.json()) as StatusSnapshot);
}

async function readDetail(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    return typeof body.detail === "string" ? body.detail : "";
  } catch {
    return "";
  }
}

function throwRunControl(detail: string): never {
  if (detail === "already_running") throw new RunControlError("already_running");
  if (detail === "missing_cookies") throw new RunControlError("missing_cookies");
  if (detail === "empty_queue") throw new RunControlError("empty_queue");
  throw new RunControlError("failed");
}

export async function startRun(): Promise<void> {
  const res = await apiFetch("/api/run/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (res.ok) return;
  throwRunControl(await readDetail(res));
}

export async function stopRun(): Promise<void> {
  const res = await apiFetch("/api/run/stop", { method: "POST" });
  if (res.ok) return;
  throwRunControl(await readDetail(res));
}

function parseWeekdays(raw: unknown): number[] {
  const fallback = [0, 1, 2, 3, 4, 5, 6];
  if (!Array.isArray(raw)) return fallback;
  const out: number[] = [];
  for (const item of raw) {
    const n = Number(item);
    if (!Number.isInteger(n) || n < 0 || n > 6) continue;
    if (!out.includes(n)) out.push(n);
  }
  return out.length > 0 ? out.sort((a, b) => a - b) : fallback;
}

function parseSchedule(raw: Partial<ScheduleSettings> & { weekdays?: unknown }): ScheduleSettings {
  return {
    enabled: Boolean(raw.enabled),
    time_msk: text(raw.time_msk) || "07:00",
    weekdays: parseWeekdays(raw.weekdays),
    last_fired_at: raw.last_fired_at ? text(raw.last_fired_at) : null,
    last_skip_reason: raw.last_skip_reason ? text(raw.last_skip_reason) : null,
    last_attempt_at: raw.last_attempt_at ? text(raw.last_attempt_at) : null,
    next_fire_at: raw.next_fire_at ? text(raw.next_fire_at) : null,
  };
}

export async function fetchSchedule(): Promise<ScheduleSettings> {
  const res = await apiFetch("/api/schedule");
  if (!res.ok) throw new Error("schedule_load_failed");
  return parseSchedule((await res.json()) as Partial<ScheduleSettings>);
}

export async function putSchedule(body: {
  enabled?: boolean;
  time_msk?: string;
  weekdays?: number[];
}): Promise<ScheduleSettings> {
  const res = await apiFetch("/api/schedule", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.status === 400) {
    const detail = await readDetail(res);
    if (detail === "invalid_weekdays") throw new Error("invalid_weekdays");
    throw new Error("invalid_time_msk");
  }
  if (!res.ok) throw new Error("schedule_save_failed");
  return parseSchedule((await res.json()) as Partial<ScheduleSettings>);
}

function parseOperatorSettings(raw: Partial<OperatorSettings> & Record<string, unknown>): OperatorSettings {
  const n = Number(raw.l1_min_price_rub);
  const rub = Number.isFinite(n) ? n : 100_000;
  const prompt = typeof raw.ai_system_prompt === "string" ? raw.ai_system_prompt : "";
  return {
    l1_min_price_rub: Math.max(0, Math.min(5_000_000, Math.round(rub))),
    ai_system_prompt: prompt,
    ai_system_prompt_is_default: Boolean(raw.ai_system_prompt_is_default ?? true),
  };
}

export async function fetchOperatorSettings(): Promise<OperatorSettings> {
  const res = await apiFetch("/api/operator-settings");
  if (!res.ok) throw new Error("operator_settings_load_failed");
  return parseOperatorSettings((await res.json()) as Partial<OperatorSettings>);
}

export async function putOperatorSettings(body: {
  l1_min_price_rub?: number;
  ai_system_prompt?: string | null;
}): Promise<OperatorSettings> {
  const res = await apiFetch("/api/operator-settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.status === 400) {
    const detail = await res.json().catch(() => ({}));
    const code = typeof detail?.detail === "string" ? detail.detail : "invalid_body";
    throw new Error(code);
  }
  if (!res.ok) throw new Error("operator_settings_save_failed");
  return parseOperatorSettings((await res.json()) as Partial<OperatorSettings>);
}

export type CookiesUploadResult = {
  platform_id: string;
  session: PlatformSession;
};

export async function postPlatformCookies(
  platformId: string,
  cookies: unknown,
): Promise<CookiesUploadResult> {
  if (!Array.isArray(cookies) || cookies.length === 0) {
    throw new Error("invalid_cookies_json");
  }
  const res = await apiFetch(`/api/platforms/${encodeURIComponent(platformId)}/cookies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cookies),
  });
  if (res.status === 400) throw new Error("invalid_cookies_json");
  if (!res.ok) throw new Error("cookies_upload_failed");
  const body = (await res.json()) as { platform_id?: string; session?: string };
  return {
    platform_id: text(body.platform_id) || platformId,
    session: parsePlatformSession(body.session),
  };
}

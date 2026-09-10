import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import {
  Alert,
  AppBar,
  Box,
  Button,
  Snackbar,
  Tab,
  Tabs,
  Toolbar,
  Typography,
} from "@mui/material";
import type {
  AppTab,
  BitrixFilter,
  DeadlinePreset,
  InboxLot,
  InboxSort,
  IngestedPreset,
  OperatorSettings,
  PlatformRow,
  PlatformSession,
  PriorityFilter,
  SalesTier,
  ScheduleSettings,
  SearchGroup,
  TeachBucket,
  TechStatus,
  ViewMode,
} from "./types";
import { copy } from "./copy";
import { deadlineQuery, ingestedQuery, mskTodayIso } from "./lib/date-filters";
import { aiBoardTier, tierMoved } from "./lib/format";
import {
  RunControlError,
  SearchControlError,
  UnauthorizedError,
  BitrixSendError,
  apiTierParam,
  createSearchGroup,
  deleteSearchGroup,
  fetchInbox,
  fetchInboxItem,
  fetchOperatorSettings,
  fetchPlatforms,
  fetchSchedule,
  fetchSearchGroups,
  fetchStatus,
  putPriority,
  postTierTeach,
  putViewed,
  postMarkAllViewed,
  putBoardHidden,
  postAiReview,
  postAiWrong,
  postBitrixSend,
  runControlMessage,
  searchControlMessage,
  setPlatformEnabled,
  startRun,
  stopRun,
  updateSearchGroup,
  type SearchGroupWrite,
} from "./lib/inbox";
import { stripe } from "./theme/palette";
import ThemeRegistry from "./theme/ThemeRegistry";
import InboxCommandBar from "./components/scout/InboxCommandBar";
import InboxExportDrawer, { type ExportPrefill } from "./components/scout/InboxExportDrawer";
import AutoSlotStatus from "./components/scout/AutoSlotStatus";
import LotBoard from "./components/scout/LotBoard";
import LotTable from "./components/scout/LotTable";
import SessionExpiryBanner from "./components/scout/SessionExpiryBanner";
import TenderDrawer from "./components/scout/TenderDrawer";
import LoginScreen from "./components/scout/LoginScreen";
import CardTextButton from "./vendor/personal/dispatch/CardTextButton";
import { fetchMe, logout } from "./lib/auth";

const ManualRunControls = lazy(() => import("./components/scout/ManualRunControls"));
const AiReviewCommandBar = lazy(() => import("./components/scout/AiReviewCommandBar"));
const SettingsPanel = lazy(() => import("./components/scout/SettingsPanel"));

const SEARCH_DEBOUNCE_MS = 300;
const STATUS_POLL_MS = 2000;

const idleTech: TechStatus = {
  phase: "idle",
  phase_label: copy.phase_idle,
  running: false,
  pipeline: "manual",
  list_done: 0,
  list_total: 0,
  cards_done: 0,
  cards_total: 0,
  counters: { L1: 0, L2: 0, L3: 0, noise: 0 },
  run_report: { new: 0, already: 0, updated: 0, expired: 0 },
  ai_failures: 0,
  ai_review_done: 0,
  ai_review_total: 0,
  http_retries: 0,
  session: "missing",
  run_dir: "",
  queue: [],
  queue_index: 0,
  queue_total: 0,
  current_search_name: "",
  log: [],
};

const idleSchedule: ScheduleSettings = {
  enabled: true,
  time_msk: "07:00",
  weekdays: [0, 1, 2, 3, 4, 5, 6],
  last_fired_at: null,
  last_skip_reason: null,
  last_attempt_at: null,
  next_fire_at: null,
};

const idleOperatorSettings: OperatorSettings = {
  l1_min_price_rub: 100_000,
  ai_system_prompt: "",
  ai_system_prompt_is_default: true,
};

function InboxEmpty({
  tab,
  kind,
}: {
  tab: "auto" | "manual";
  kind: "no-data" | "no-match" | "no-unread" | "error";
}) {
  const title =
    tab === "auto"
      ? kind === "error"
        ? copy.error_auto_load_title
        : kind === "no-unread"
          ? copy.empty_auto_no_unread_title
          : kind === "no-match"
            ? copy.empty_auto_no_match_title
            : copy.empty_auto_title
      : kind === "error"
        ? copy.error_manual_load_title
        : kind === "no-unread"
          ? copy.empty_no_unread_title
          : kind === "no-match"
            ? copy.empty_no_match_title
            : copy.empty_manual_title;
  const body =
    tab === "auto"
      ? kind === "error"
        ? copy.error_auto_load_body
        : kind === "no-unread"
          ? copy.empty_auto_no_unread_body
          : kind === "no-match"
            ? copy.empty_auto_no_match_body
            : copy.empty_auto_body
      : kind === "error"
        ? copy.error_manual_load_body
        : kind === "no-unread"
          ? copy.empty_no_unread_body
          : kind === "no-match"
            ? copy.empty_no_match_body
            : copy.empty_manual_body;
  return (
    <Box sx={{ textAlign: "center", py: 6, px: 2 }}>
      <Typography variant="h2" sx={{ mb: 0.5 }}>
        {title}
      </Typography>
      <Typography color="text.secondary">{body}</Typography>
    </Box>
  );
}

function AppInner() {
  const [gate, setGate] = useState<"loading" | "anon" | "in">("loading");
  const [tab, setTab] = useState<AppTab>("auto");
  const [lots, setLots] = useState<InboxLot[]>([]);
  const [lotsState, setLotsState] = useState<"idle" | "loading" | "ok" | "error">("idle");
  const [view, setView] = useState<ViewMode>("cards");
  const [sort, setSort] = useState<InboxSort>("relevance");
  const [unreadOnly, setUnreadOnly] = useState(true);
  const [lotsEpoch, setLotsEpoch] = useState(0);
  const [aiReviewedOnly, setAiReviewedOnly] = useState(false);
  const [aiBusy, setAiBusy] = useState(false);
  const [priority, setPriority] = useState<PriorityFilter>([]);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [deadlinePreset, setDeadlinePreset] = useState<DeadlinePreset>("any");
  const [deadlineFrom, setDeadlineFrom] = useState("");
  const [deadlineTo, setDeadlineTo] = useState("");
  const [ingestedPreset, setIngestedPreset] = useState<IngestedPreset>("any");
  const [ingestedFrom, setIngestedFrom] = useState("");
  const [ingestedTo, setIngestedTo] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [tech, setTech] = useState<TechStatus>(idleTech);
  const [techBusy, setTechBusy] = useState(false);
  const [techError, setTechError] = useState<string | null>(null);
  const [groups, setGroups] = useState<SearchGroup[]>([]);
  const [platforms, setPlatforms] = useState<PlatformRow[]>([]);
  const [schedule, setSchedule] = useState<ScheduleSettings>(idleSchedule);
  const [operatorSettings, setOperatorSettings] = useState<OperatorSettings>(idleOperatorSettings);
  const [priceMinRub, setPriceMinRub] = useState<number | null>(null);
  const [operatorSettingsReady, setOperatorSettingsReady] = useState(false);
  const priceFilterInitialized = useRef(false);
  const [platformsSelected, setPlatformsSelected] = useState<string[]>([]);
  const [bitrixFilter, setBitrixFilter] = useState<BitrixFilter>("any");
  const [exportOpen, setExportOpen] = useState(false);
  const [exportPrefill, setExportPrefill] = useState<ExportPrefill | null>(null);
  const [groupError, setGroupError] = useState<string | null>(null);
  const [highlightSessions, setHighlightSessions] = useState(false);
  const prevRunningRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    fetchMe().then((me) => {
      if (!cancelled) setGate(me ? "in" : "anon");
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [search]);

  function onUnauthorized() {
    setGate("anon");
    setLots([]);
    setSelectedId(null);
    setLotsState("idle");
    setOperatorSettingsReady(false);
    priceFilterInitialized.current = false;
    setPriceMinRub(null);
  }

  function inboxQuery() {
    const today = mskTodayIso();
    const dates = {
      ...deadlineQuery(deadlinePreset, deadlineFrom, deadlineTo, today),
      ...ingestedQuery(ingestedPreset, ingestedFrom, ingestedTo, today),
    };
    return {
      unread: unreadOnly ? true : undefined,
      ai_reviewed: tab === "auto" || (tab === "manual" && aiReviewedOnly) ? true : undefined,
      ai_trigger: tab === "auto" ? ("auto" as const) : undefined,
      tier: apiTierParam(priority),
      q: debouncedSearch || undefined,
      price_min_rub: priceMinRub ?? undefined,
      platform: platformsSelected.length > 0 ? platformsSelected.join(",") : undefined,
      bitrix: bitrixFilter === "any" ? undefined : bitrixFilter,
      sort,
      ...dates,
    };
  }

  function openExportDrawer() {
    setExportPrefill({ ...inboxQuery() });
    setExportOpen(true);
  }

  useEffect(() => {
    if (gate !== "in") return;
    if (tab !== "auto" && tab !== "manual") return;
    if (!operatorSettingsReady) return;
    let cancelled = false;
    setLotsState((prev) => (prev === "ok" ? prev : "loading"));
    fetchInbox(inboxQuery())
      .then((items) => {
        if (cancelled) return;
        setLots(items);
        setLotsState("ok");
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) {
          onUnauthorized();
          return;
        }
        setLotsState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [
    gate,
    tab,
    unreadOnly,
    lotsEpoch,
    aiReviewedOnly,
    priority,
    debouncedSearch,
    deadlinePreset,
    deadlineFrom,
    deadlineTo,
    ingestedPreset,
    ingestedFrom,
    ingestedTo,
    priceMinRub,
    platformsSelected,
    bitrixFilter,
    sort,
    operatorSettingsReady,
  ]);

  useEffect(() => {
    if (gate !== "in" || !selectedId) return;
    let cancelled = false;
    fetchInboxItem(selectedId)
      .then((item) => {
        if (cancelled) return;
        setLots((prev) => {
          const exists = prev.some((lot) => lot.tender_id === item.tender_id);
          if (!exists) return prev;
          return prev.map((lot) => (lot.tender_id === item.tender_id ? item : lot));
        });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) onUnauthorized();
      });
    return () => {
      cancelled = true;
    };
  }, [gate, selectedId]);

  useEffect(() => {
    if (gate !== "in") return;
    let cancelled = false;
    let timer: number | undefined;

    const tick = () => {
      Promise.all([
        fetchStatus(),
        fetchSearchGroups(),
        fetchPlatforms(),
        fetchSchedule().catch((err: unknown) => {
          if (err instanceof UnauthorizedError) throw err;
          return null;
        }),
      ])
        .then(([status, groupItems, platformItems, scheduleItem]) => {
          if (cancelled) return;
          setTech(status);
          setGroups(groupItems);
          setPlatforms(platformItems);
          if (scheduleItem) setSchedule(scheduleItem);
          timer = window.setTimeout(tick, status.running ? STATUS_POLL_MS : STATUS_POLL_MS * 4);
        })
        .catch((err: unknown) => {
          if (cancelled) return;
          if (err instanceof UnauthorizedError) {
            onUnauthorized();
            return;
          }
          timer = window.setTimeout(tick, STATUS_POLL_MS * 4);
        });
    };
    tick();
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [gate]);

  useEffect(() => {
    if (gate !== "in") return;
    let cancelled = false;
    fetchOperatorSettings()
      .then((settings) => {
        if (cancelled) return;
        setOperatorSettings(settings);
        if (!priceFilterInitialized.current) {
          setPriceMinRub(settings.l1_min_price_rub);
          priceFilterInitialized.current = true;
        }
        setOperatorSettingsReady(true);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) {
          onUnauthorized();
          return;
        }
        if (!priceFilterInitialized.current) {
          setPriceMinRub(idleOperatorSettings.l1_min_price_rub);
          priceFilterInitialized.current = true;
        }
        setOperatorSettingsReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, [gate]);

  async function onStartRun() {
    setTechBusy(true);
    setTechError(null);
    try {
      await startRun();
      const status = await fetchStatus();
      setTech(status);
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return;
      }
      setTechError(
        err instanceof RunControlError ? runControlMessage(err.code) : copy.run_error_failed,
      );
    } finally {
      setTechBusy(false);
    }
  }

  function replaceGroup(next: SearchGroup) {
    setGroups((prev) => {
      const exists = prev.some((row) => row.id === next.id);
      if (!exists) return [...prev, next];
      return prev.map((row) => (row.id === next.id ? next : row));
    });
  }

  function replacePlatform(next: PlatformRow) {
    setPlatforms((prev) => {
      const exists = prev.some((row) => row.platform_id === next.platform_id);
      if (!exists) return [...prev, next];
      return prev.map((row) => (row.platform_id === next.platform_id ? next : row));
    });
  }

  async function onToggleQueue(group: SearchGroup, inQueue: boolean) {
    setGroupError(null);
    try {
      replaceGroup(
        await updateSearchGroup(group.id, {
          name: group.name,
          queries: group.queries,
          exclude: group.exclude,
          limit_n: group.limit_n,
          in_queue: inQueue,
          sort_order: group.sort_order,
        }),
      );
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return;
      }
      setGroupError(
        err instanceof SearchControlError ? searchControlMessage(err.code) : copy.groups_save_failed,
      );
    }
  }

  async function onTogglePlatform(platform: PlatformRow, enabled: boolean) {
    setGroupError(null);
    try {
      replacePlatform(await setPlatformEnabled(platform.platform_id, enabled));
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return;
      }
      setGroupError(copy.groups_save_failed);
    }
  }

  async function onSaveGroup(id: string | undefined, body: SearchGroupWrite) {
    setGroupError(null);
    try {
      const saved = id ? await updateSearchGroup(id, body) : await createSearchGroup(body);
      if (id) replaceGroup(saved);
      else setGroups((prev) => [...prev, saved]);
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        throw err;
      }
      setGroupError(
        err instanceof SearchControlError ? searchControlMessage(err.code) : copy.groups_save_failed,
      );
      throw err;
    }
  }

  async function onDeleteGroup(group: SearchGroup) {
    setGroupError(null);
    try {
      await deleteSearchGroup(group.id);
      setGroups((prev) => prev.filter((row) => row.id !== group.id));
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return;
      }
      setGroupError(copy.groups_save_failed);
    }
  }

  async function onStopRun() {
    setTechBusy(true);
    setTechError(null);
    try {
      await stopRun();
      const status = await fetchStatus();
      setTech(status);
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return;
      }
      setTechError(
        err instanceof RunControlError ? runControlMessage(err.code) : copy.run_error_failed,
      );
    } finally {
      setTechBusy(false);
    }
  }

  const filtered = useMemo(() => {
    const visible = lots.filter((lot) => !lot.board_hidden);
    if (priority.length < 2) return visible;
    return visible.filter((lot) => priority.includes(aiBoardTier(lot)));
  }, [lots, priority]);

  const selected = lots.find((l) => l.tender_id === selectedId) ?? null;
  const visibleLots = lots.filter((lot) => !lot.board_hidden);
  const hasActiveFilters =
    Boolean(debouncedSearch) ||
    deadlinePreset !== "any" ||
    ingestedPreset !== "any" ||
    priority.length > 0 ||
    (priceMinRub != null && priceMinRub > 0) ||
    platformsSelected.length > 0 ||
    bitrixFilter !== "any" ||
    (tab === "manual" && aiReviewedOnly);
  const emptyKind: "error" | "no-unread" | "no-data" | "no-match" =
    lotsState === "error"
      ? "error"
      : visibleLots.length === 0
        ? unreadOnly && !hasActiveFilters
          ? "no-unread"
          : hasActiveFilters
            ? "no-match"
            : "no-data"
        : "no-match";

  function replaceLot(next: InboxLot) {
    setLots((prev) => prev.map((lot) => (lot.tender_id === next.tender_id ? next : lot)));
  }

  async function onToggleViewed(id: string) {
    const current = lots.find((lot) => lot.tender_id === id);
    if (!current) return;
    try {
      replaceLot(await putViewed(id, !current.viewed));
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return;
      }
      setToast(copy.error_viewed_save);
    }
  }

  function markAllViewedScope(): { ai_reviewed?: boolean; ai_trigger?: "auto" } {
    if (tab === "auto") return { ai_reviewed: true, ai_trigger: "auto" };
    return {};
  }

  async function onCountUnreadInTab(): Promise<number> {
    try {
      const { count } = await postMarkAllViewed({ dry_run: true, ...markAllViewedScope() });
      return count;
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return 0;
      }
      setToast(copy.mark_all_viewed_failed);
      throw err;
    }
  }

  async function onMarkAllUnreadInTab(): Promise<number> {
    try {
      const { updated } = await postMarkAllViewed({ dry_run: false, ...markAllViewedScope() });
      setLotsEpoch((n) => n + 1);
      setToast(copy.mark_all_viewed_done.replace("{n}", String(updated)));
      return updated;
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return 0;
      }
      setToast(copy.mark_all_viewed_failed);
      throw err;
    }
  }

  async function onSetPriority(id: string, tier: SalesTier | null) {
    try {
      replaceLot(await putPriority(id, tier));
      setToast(copy.override_done);
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return;
      }
      setToast(copy.error_priority_save);
    }
  }

  async function onTierTeach(args: {
    tender_id: string;
    from_bucket: TeachBucket;
    to_bucket: TeachBucket;
    drop_tier_correct: boolean;
    reason_ru: string;
  }) {
    try {
      const { lot } = await postTierTeach(args.tender_id, {
        from_bucket: args.from_bucket,
        to_bucket: args.to_bucket,
        drop_tier_correct: args.drop_tier_correct,
        reason_ru: args.reason_ru,
      });
      replaceLot(lot);
      setToast(copy.teach_saved);
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        throw err;
      }
      setToast(copy.teach_save_failed);
      throw err;
    }
  }

  async function onSetBoardHidden(id: string, hidden: boolean) {
    try {
      replaceLot(await putBoardHidden(id, hidden));
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return;
      }
      setToast(copy.error_archive_save);
    }
  }

  async function reloadInbox() {
    const items = await fetchInbox(inboxQuery());
    setLots(items);
    setLotsState("ok");
    return items;
  }

  useEffect(() => {
    if (gate !== "in") return;
    if (tab !== "auto" && tab !== "manual") return;
    const wasRunning = prevRunningRef.current;
    prevRunningRef.current = tech.running;
    if (!wasRunning || tech.running) return;
    if (tech.phase !== "done" && tech.phase !== "partial") return;
    let cancelled = false;
    reloadInbox()
      .then(() => undefined)
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) onUnauthorized();
      });
    return () => {
      cancelled = true;
    };
  }, [gate, tab, tech.running, tech.phase]);

  async function onAiReview(opts?: { retryErrors?: boolean }) {
    setAiBusy(true);
    try {
      const result = await postAiReview(
        opts?.retryErrors ? { retryErrors: true } : undefined,
      );
      const moved = result.items.filter((item) => tierMoved(item)).length;
      if (tab === "manual") {
        await reloadInbox();
      } else if (result.items.length) {
        setLots((prev) => {
          const byId = new Map(result.items.map((item) => [item.tender_id, item]));
          return prev.map((lot) => byId.get(lot.tender_id) ?? lot);
        });
      }
      if (result.failed > 0) {
        setToast(
          copy.ai_review_toast_failed
            .replace("{n}", String(result.processed))
            .replace("{m}", String(result.failed)),
        );
      } else {
        setToast(
          copy.ai_review_toast.replace("{n}", String(result.processed)).replace("{m}", String(moved)),
        );
      }
      const status = await fetchStatus();
      setTech(status);
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return;
      }
      setToast(copy.error_ai_action);
    } finally {
      setAiBusy(false);
    }
  }

  async function onAiWrong(id: string) {
    try {
      replaceLot(await postAiWrong(id));
      setToast(copy.action_ai_wrong);
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return;
      }
      setToast(copy.error_ai_action);
    }
  }

  async function onBitrixSend(id: string) {
    try {
      const { item } = await postBitrixSend(id);
      replaceLot(item);
      setToast(copy.bitrix_sent_ok);
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return;
      }
      if (err instanceof BitrixSendError) {
        if (err.code === "already_sent") {
          setToast(copy.bitrix_already);
          return;
        }
        if (err.code === "bitrix_unconfigured") {
          setToast(copy.bitrix_unconfigured);
          return;
        }
        setToast(copy.bitrix_error);
        return;
      }
      setToast(copy.bitrix_error);
    }
  }

  function onCookieSession(platformId: string, session: PlatformSession) {
    setPlatforms((prev) =>
      prev.map((row) => (row.platform_id === platformId ? { ...row, session } : row)),
    );
  }

  if (gate === "loading") {
    return <Box sx={{ minHeight: "100vh", bgcolor: stripe.surfaceSubtle }} />;
  }
  if (gate === "anon") {
    return <LoginScreen onSuccess={() => setGate("in")} />;
  }

  const lotsLoading = lotsState === "loading" || lotsState === "idle";
  const queuedGroups = groups.filter((row) => row.in_queue).length;
  const enabledPlatforms = platforms.filter((row) => row.enabled).length;
  const settingsLocked = techBusy || tech.running;

  const commandBar = (
    <InboxCommandBar
      unreadOnly={unreadOnly}
      onUnreadOnly={setUnreadOnly}
      onCountUnreadInTab={tab === "auto" || tab === "manual" ? onCountUnreadInTab : undefined}
      onMarkAllUnreadInTab={tab === "auto" || tab === "manual" ? onMarkAllUnreadInTab : undefined}
      priority={priority}
      onPriority={setPriority}
      search={search}
      onSearch={setSearch}
      deadlinePreset={deadlinePreset}
      onDeadlinePreset={setDeadlinePreset}
      deadlineFrom={deadlineFrom}
      onDeadlineFrom={setDeadlineFrom}
      deadlineTo={deadlineTo}
      onDeadlineTo={setDeadlineTo}
      ingestedPreset={ingestedPreset}
      onIngestedPreset={setIngestedPreset}
      ingestedFrom={ingestedFrom}
      onIngestedFrom={setIngestedFrom}
      ingestedTo={ingestedTo}
      onIngestedTo={setIngestedTo}
      view={view}
      onView={setView}
      sort={sort}
      onSort={setSort}
      showAiReviewedFilter={tab === "manual"}
      aiReviewedOnly={aiReviewedOnly}
      onAiReviewedOnly={setAiReviewedOnly}
      priceMinRub={priceMinRub}
      onPriceMinRub={setPriceMinRub}
      settingsMinPrice={operatorSettings.l1_min_price_rub}
      onOpenSettings={() => setTab("settings")}
      platforms={platforms}
      platformsSelected={platformsSelected}
      onPlatformsSelected={setPlatformsSelected}
      bitrixFilter={bitrixFilter}
      onBitrixFilter={setBitrixFilter}
      onExport={openExportDrawer}
    />
  );

  function renderBoard(mode: "auto" | "manual") {
    if (lotsState === "error") return <InboxEmpty tab={mode} kind="error" />;
    if (lotsLoading) return <Box sx={{ flex: 1, bgcolor: stripe.surfaceSubtle }} />;
    if (filtered.length === 0) return <InboxEmpty tab={mode} kind={emptyKind} />;
    if (view === "cards") {
      return (
        <LotBoard
          lots={filtered}
          selectedId={selectedId}
          onOpen={setSelectedId}
          boardTier={aiBoardTier}
          showTierMove
          sort={sort}
          onTeachSubmit={onTierTeach}
        />
      );
    }
    return (
      <LotTable
        lots={filtered}
        selectedId={selectedId}
        onOpen={setSelectedId}
        boardTier={aiBoardTier}
        showTierMove
        sort={sort}
        onSort={setSort}
      />
    );
  }

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default", display: "flex", flexDirection: "column" }}>
      <AppBar
        position="static"
        elevation={0}
        color="inherit"
        sx={{ borderBottom: `1px solid ${stripe.border}`, bgcolor: stripe.surface }}
      >
        <Toolbar sx={{ minHeight: 48, gap: 1, py: 1, flexWrap: "wrap" }}>
          <Box
            component="img"
            src="/brand/logo.png"
            alt=""
            sx={{ width: 28, height: 28, flexShrink: 0 }}
          />
          <Typography variant="h2" sx={{ flexGrow: 1, minWidth: 0 }}>
            {copy.product_title}
          </Typography>
          <CardTextButton
            onClick={async () => {
              await logout();
              setGate("anon");
              setLots([]);
              setSelectedId(null);
            }}
          >
            {copy.login_logout}
          </CardTextButton>
        </Toolbar>
        <Tabs
          value={tab}
          onChange={(_, v: AppTab) => {
            setTab(v);
            setSelectedId(null);
            if (v !== "settings") setHighlightSessions(false);
          }}
          sx={{ px: 2, minHeight: 32 }}
        >
          <Tab label={copy.tab_auto} value="auto" />
          <Tab label={copy.tab_manual} value="manual" />
          <Tab label={copy.tab_settings} value="settings" />
        </Tabs>
      </AppBar>

      <Box sx={{ p: 2, flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        {tab === "auto" ? (
          <>
            <SessionExpiryBanner
              platforms={platforms}
              onOpenSettings={() => {
                setHighlightSessions(true);
                setTab("settings");
              }}
            />
            <AutoSlotStatus schedule={schedule} status={tech} />
            {tech.ai_failures > 0 ? (
              <Alert
                severity="warning"
                sx={{ mb: 1.5, py: 0.5 }}
                action={
                  <Button
                    color="inherit"
                    size="small"
                    onClick={() => {
                      setTab("manual");
                      setSelectedId(null);
                    }}
                  >
                    {copy.tab_manual}
                  </Button>
                }
              >
                {copy.ai_auto_incomplete.replace("{n}", String(tech.ai_failures))}
              </Alert>
            ) : null}
            <Typography variant="body2" sx={{ color: stripe.textMuted, mb: 1.5 }}>
              {copy.auto_lead_hint}
            </Typography>
            <Box sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
              {commandBar}
              {renderBoard("auto")}
            </Box>
            {selected ? (
              <TenderDrawer
                lot={selected}
                drawerMode="ai"
                onClose={() => setSelectedId(null)}
                onToggleViewed={onToggleViewed}
                onSetPriority={onSetPriority}
                onSetBoardHidden={onSetBoardHidden}
                onAiWrong={(id) => void onAiWrong(id)}
                onBitrixSend={onBitrixSend}
              />
            ) : null}
          </>
        ) : tab === "manual" ? (
          <Suspense fallback={<Box sx={{ flex: 1, bgcolor: stripe.surfaceSubtle }} />}>
            <ManualRunControls
              status={tech}
              queuedGroups={queuedGroups}
              enabledPlatforms={enabledPlatforms}
              busy={techBusy}
              error={techError}
              onStart={onStartRun}
              onStop={onStopRun}
            />
            <AiReviewCommandBar
              onAiReview={() => void onAiReview()}
              onRetryErrors={() => void onAiReview({ retryErrors: true })}
              aiBusy={aiBusy}
              aiDone={tech.ai_review_done}
              aiTotal={tech.ai_review_total}
              aiFailures={tech.ai_failures}
            />
            <Typography variant="body2" sx={{ color: stripe.textMuted, mb: 1 }}>
              {copy.manual_lead_hint} {copy.manual_session_muted}
            </Typography>
            <Box sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
              {commandBar}
              {renderBoard("manual")}
            </Box>
            {selected ? (
              <TenderDrawer
                lot={selected}
                drawerMode="ai"
                onClose={() => setSelectedId(null)}
                onToggleViewed={onToggleViewed}
                onSetPriority={onSetPriority}
                onSetBoardHidden={onSetBoardHidden}
                onAiWrong={(id) => void onAiWrong(id)}
                onBitrixSend={onBitrixSend}
              />
            ) : null}
          </Suspense>
        ) : (
          <Suspense fallback={<Box sx={{ flex: 1, bgcolor: stripe.surfaceSubtle }} />}>
            <SettingsPanel
              status={tech}
              schedule={schedule}
              operatorSettings={operatorSettings}
              groups={groups}
              platforms={platforms}
              locked={settingsLocked}
              groupError={groupError}
              highlightSessions={highlightSessions}
              onScheduleSaved={setSchedule}
              onOperatorSettingsSaved={(next) => {
                setOperatorSettings(next);
                setPriceMinRub(next.l1_min_price_rub);
              }}
              onToggleQueue={onToggleQueue}
              onTogglePlatform={onTogglePlatform}
              onSaveGroup={onSaveGroup}
              onDeleteGroup={onDeleteGroup}
              onCookieSession={onCookieSession}
            />
          </Suspense>
        )}
      </Box>

      <Snackbar
        open={Boolean(toast)}
        autoHideDuration={1600}
        onClose={() => setToast(null)}
        message={toast}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      />
      {exportPrefill ? (
        <InboxExportDrawer
          open={exportOpen}
          onClose={() => setExportOpen(false)}
          prefill={exportPrefill}
          onUnauthorized={onUnauthorized}
          onError={(message) => setToast(message)}
        />
      ) : null}
    </Box>
  );
}

export default function App() {
  return (
    <ThemeRegistry>
      <AppInner />
    </ThemeRegistry>
  );
}

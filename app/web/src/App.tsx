import { useEffect, useMemo, useState } from "react";
import {
  AppBar,
  Box,
  Snackbar,
  Tab,
  Tabs,
  Toolbar,
  Typography,
} from "@mui/material";
import type {
  AppTab,
  DeadlinePreset,
  InboxLot,
  IngestedPreset,
  PlatformRow,
  PlatformSession,
  PriorityFilter,
  SalesTier,
  ScheduleSettings,
  SearchGroup,
  TechStatus,
  ViewMode,
} from "./types";
import { copy } from "./copy";
import { deadlineQuery, ingestedQuery, mskTodayIso } from "./lib/date-filters";
import { aiBoardTier, rulesBoardTier, tierMoved } from "./lib/format";
import {
  RunControlError,
  SearchControlError,
  UnauthorizedError,
  apiTierParam,
  createSearchGroup,
  deleteSearchGroup,
  fetchInbox,
  fetchInboxItem,
  fetchPlatforms,
  fetchSchedule,
  fetchSearchGroups,
  fetchStatus,
  putPriority,
  putViewed,
  putBoardHidden,
  postAiReview,
  postAiWrong,
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
import AiReviewCommandBar from "./components/scout/AiReviewCommandBar";
import AutoSlotStatus from "./components/scout/AutoSlotStatus";
import LotBoard from "./components/scout/LotBoard";
import LotTable from "./components/scout/LotTable";
import ManualRunControls from "./components/scout/ManualRunControls";
import SessionExpiryBanner from "./components/scout/SessionExpiryBanner";
import SettingsPanel from "./components/scout/SettingsPanel";
import TenderDrawer from "./components/scout/TenderDrawer";
import LoginScreen from "./components/scout/LoginScreen";
import CardTextButton from "./vendor/personal/dispatch/CardTextButton";
import { fetchMe, logout } from "./lib/auth";

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
  last_fired_at: null,
  last_skip_reason: null,
  last_attempt_at: null,
  next_fire_at: null,
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
  const [unreadOnly, setUnreadOnly] = useState(true);
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
  const [groupError, setGroupError] = useState<string | null>(null);
  const [highlightSessions, setHighlightSessions] = useState(false);

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
      ...dates,
    };
  }

  useEffect(() => {
    if (gate !== "in") return;
    if (tab !== "auto" && tab !== "manual") return;
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
    aiReviewedOnly,
    priority,
    debouncedSearch,
    deadlinePreset,
    deadlineFrom,
    deadlineTo,
    ingestedPreset,
    ingestedFrom,
    ingestedTo,
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

  const boardTierFn = tab === "auto" ? aiBoardTier : rulesBoardTier;

  const filtered = useMemo(() => {
    const visible = lots.filter((lot) => !lot.board_hidden);
    if (priority.length < 2) return visible;
    return visible.filter((lot) => priority.includes(boardTierFn(lot)));
  }, [lots, priority, boardTierFn]);

  const selected = lots.find((l) => l.tender_id === selectedId) ?? null;
  const emptyKind: "error" | "no-unread" | "no-data" | "no-match" =
    lotsState === "error"
      ? "error"
      : lots.filter((l) => !l.board_hidden).length === 0
        ? unreadOnly && !debouncedSearch && deadlinePreset === "any" && ingestedPreset === "any"
          ? "no-unread"
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
      if (err instanceof UnauthorizedError) onUnauthorized();
    }
  }

  async function onSetPriority(id: string, tier: SalesTier | null) {
    try {
      replaceLot(await putPriority(id, tier));
      setToast(copy.override_done);
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) onUnauthorized();
    }
  }

  async function onSetBoardHidden(id: string, hidden: boolean) {
    try {
      replaceLot(await putBoardHidden(id, hidden));
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) onUnauthorized();
    }
  }

  async function reloadInbox() {
    const items = await fetchInbox(inboxQuery());
    setLots(items);
    setLotsState("ok");
    return items;
  }

  async function onAiReview() {
    setAiBusy(true);
    try {
      const result = await postAiReview();
      const moved = result.items.filter((item) => tierMoved(item)).length;
      if (tab === "manual") {
        await reloadInbox();
      } else if (result.items.length) {
        setLots((prev) => {
          const byId = new Map(result.items.map((item) => [item.tender_id, item]));
          return prev.map((lot) => byId.get(lot.tender_id) ?? lot);
        });
      }
      setToast(copy.ai_review_toast.replace("{n}", String(result.processed)).replace("{m}", String(moved)));
      const status = await fetchStatus();
      setTech(status);
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) onUnauthorized();
    } finally {
      setAiBusy(false);
    }
  }

  async function onAiWrong(id: string) {
    try {
      replaceLot(await postAiWrong(id));
      setToast(copy.action_ai_wrong);
    } catch (err: unknown) {
      if (err instanceof UnauthorizedError) onUnauthorized();
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
      showAiReviewedFilter={tab === "manual"}
      aiReviewedOnly={aiReviewedOnly}
      onAiReviewedOnly={setAiReviewedOnly}
    />
  );

  function renderBoard(mode: "auto" | "manual") {
    const boardTier = mode === "auto" ? aiBoardTier : rulesBoardTier;
    if (lotsState === "error") return <InboxEmpty tab={mode} kind="error" />;
    if (lotsLoading) return <Box sx={{ flex: 1, bgcolor: stripe.surfaceSubtle }} />;
    if (filtered.length === 0) return <InboxEmpty tab={mode} kind={emptyKind} />;
    if (view === "cards") {
      return (
        <LotBoard
          lots={filtered}
          selectedId={selectedId}
          onOpen={setSelectedId}
          boardTier={boardTier}
          showAiHint={mode === "manual"}
          showTierMove={mode === "auto"}
        />
      );
    }
    return (
      <LotTable
        lots={filtered}
        selectedId={selectedId}
        onOpen={setSelectedId}
        boardTier={boardTier}
        showTierMove={mode === "auto"}
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
            <Typography variant="body2" sx={{ color: stripe.textMuted, mb: 1.5 }}>
              {copy.auto_mail_hint}
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
              />
            ) : null}
          </>
        ) : tab === "manual" ? (
          <>
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
              aiBusy={aiBusy}
              aiDone={tech.ai_review_done}
              aiTotal={tech.ai_review_total}
            />
            <Typography variant="body2" sx={{ color: stripe.textMuted, mb: 1 }}>
              {copy.manual_no_mail_hint} {copy.manual_session_muted}
            </Typography>
            <Box sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
              {commandBar}
              {renderBoard("manual")}
            </Box>
            {selected ? (
              <TenderDrawer
                lot={selected}
                drawerMode="rules"
                onClose={() => setSelectedId(null)}
                onToggleViewed={onToggleViewed}
                onSetPriority={onSetPriority}
                onSetBoardHidden={onSetBoardHidden}
                onAiWrong={(id) => void onAiWrong(id)}
              />
            ) : null}
          </>
        ) : (
          <SettingsPanel
            status={tech}
            schedule={schedule}
            groups={groups}
            platforms={platforms}
            locked={settingsLocked}
            groupError={groupError}
            highlightSessions={highlightSessions}
            onScheduleSaved={setSchedule}
            onToggleQueue={onToggleQueue}
            onTogglePlatform={onTogglePlatform}
            onSaveGroup={onSaveGroup}
            onDeleteGroup={onDeleteGroup}
            onCookieSession={onCookieSession}
          />
        )}
      </Box>

      <Snackbar
        open={Boolean(toast)}
        autoHideDuration={1600}
        onClose={() => setToast(null)}
        message={toast}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      />
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

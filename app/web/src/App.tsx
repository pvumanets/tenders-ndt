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
  PriorityFilter,
  SalesTier,
  TechStatus,
  ViewMode,
} from "./types";
import { copy } from "./copy";
import { deadlineQuery, ingestedQuery, mskTodayIso } from "./lib/date-filters";
import { effectiveTier } from "./lib/format";
import {
  RunControlError,
  UnauthorizedError,
  apiTierParam,
  fetchInbox,
  fetchInboxItem,
  fetchStatus,
  putPriority,
  putViewed,
  runControlMessage,
  startRun,
  stopRun,
} from "./lib/inbox";
import { stripe } from "./theme/palette";
import ThemeRegistry from "./theme/ThemeRegistry";
import InboxCommandBar from "./components/scout/InboxCommandBar";
import LotBoard from "./components/scout/LotBoard";
import LotTable from "./components/scout/LotTable";
import TenderDrawer from "./components/scout/TenderDrawer";
import TechRunPanel from "./components/scout/TechRunPanel";
import LoginScreen from "./components/scout/LoginScreen";
import CardTextButton from "./vendor/personal/dispatch/CardTextButton";
import { fetchMe, logout } from "./lib/auth";

const SEARCH_DEBOUNCE_MS = 300;
const STATUS_POLL_MS = 2000;

const idleTech: TechStatus = {
  phase: "idle",
  phase_label: copy.phase_idle,
  running: false,
  list_done: 0,
  list_total: 0,
  cards_done: 0,
  cards_total: 0,
  counters: { L1: 0, L2: 0, L3: 0, noise: 0 },
  session: "missing",
  run_dir: "",
  log: [],
};

function InboxEmpty({
  kind,
}: {
  kind: "no-data" | "no-match" | "no-unread" | "error";
}) {
  const title =
    kind === "error"
      ? copy.error_load_title
      : kind === "no-unread"
        ? copy.empty_no_unread_title
        : kind === "no-match"
          ? copy.empty_no_match_title
          : copy.empty_no_data_title;
  const body =
    kind === "error"
      ? copy.error_load_body
      : kind === "no-unread"
        ? copy.empty_no_unread_body
        : kind === "no-match"
          ? copy.empty_no_match_body
          : copy.empty_no_data_body;
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
  const [tab, setTab] = useState<AppTab>("lots");
  const [lots, setLots] = useState<InboxLot[]>([]);
  const [lotsState, setLotsState] = useState<"idle" | "loading" | "ok" | "error">("idle");
  const [view, setView] = useState<ViewMode>("cards");
  const [unreadOnly, setUnreadOnly] = useState(true);
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

  useEffect(() => {
    if (gate !== "in") return;
    let cancelled = false;
    setLotsState((prev) => (prev === "ok" ? prev : "loading"));
    const today = mskTodayIso();
    const dates = {
      ...deadlineQuery(deadlinePreset, deadlineFrom, deadlineTo, today),
      ...ingestedQuery(ingestedPreset, ingestedFrom, ingestedTo, today),
    };
    fetchInbox({
      unread: unreadOnly || undefined,
      tier: apiTierParam(priority),
      q: debouncedSearch || undefined,
      ...dates,
    })
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
    unreadOnly,
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
    if (gate !== "in" || tab !== "run") return;
    let cancelled = false;
    let timer: number | undefined;

    const tick = () => {
      fetchStatus()
        .then((status) => {
          if (cancelled) return;
          setTech(status);
          timer = window.setTimeout(tick, status.running ? STATUS_POLL_MS : STATUS_POLL_MS * 4);
        })
        .catch((err: unknown) => {
          if (cancelled) return;
          if (err instanceof UnauthorizedError) onUnauthorized();
        });
    };
    tick();
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [gate, tab]);

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
    if (priority.length < 2) return lots;
    return lots.filter((lot) => priority.includes(effectiveTier(lot)));
  }, [lots, priority]);

  const selected = lots.find((l) => l.tender_id === selectedId) ?? null;
  const emptyKind =
    lotsState === "error"
      ? "error"
      : lots.length === 0
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

  if (gate === "loading") {
    return <Box sx={{ minHeight: "100vh", bgcolor: stripe.surfaceSubtle }} />;
  }
  if (gate === "anon") {
    return <LoginScreen onSuccess={() => setGate("in")} />;
  }

  const lotsLoading = lotsState === "loading" || lotsState === "idle";

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default", display: "flex", flexDirection: "column" }}>
      <AppBar
        position="static"
        elevation={0}
        color="inherit"
        sx={{ borderBottom: `1px solid ${stripe.border}`, bgcolor: stripe.surface }}
      >
        <Toolbar sx={{ minHeight: 48, gap: 1, py: 1, flexWrap: "wrap" }}>
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
          onChange={(_, v: AppTab) => setTab(v)}
          sx={{ px: 2, minHeight: 32 }}
        >
          <Tab label={copy.tab_lots} value="lots" />
          <Tab label={copy.tab_run} value="run" />
        </Tabs>
      </AppBar>

      <Box sx={{ p: 2, flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        {tab === "lots" ? (
          <>
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
            />
            {lotsState === "error" ? (
              <InboxEmpty kind="error" />
            ) : lotsLoading ? (
              <Box sx={{ flex: 1, bgcolor: stripe.surfaceSubtle }} />
            ) : filtered.length === 0 ? (
              <InboxEmpty kind={emptyKind} />
            ) : view === "cards" ? (
              <LotBoard lots={filtered} selectedId={selectedId} onOpen={setSelectedId} />
            ) : (
              <LotTable lots={filtered} selectedId={selectedId} onOpen={setSelectedId} />
            )}
            {selected ? (
              <TenderDrawer
                lot={selected}
                onClose={() => setSelectedId(null)}
                onToggleViewed={onToggleViewed}
                onSetPriority={onSetPriority}
              />
            ) : null}
          </>
        ) : (
          <TechRunPanel
            status={tech}
            busy={techBusy}
            error={techError}
            onStart={onStartRun}
            onStop={onStopRun}
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

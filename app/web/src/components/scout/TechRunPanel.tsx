import type { ReactNode } from "react";
import { useState } from "react";
import { Alert, Box, Paper, Stack, Typography } from "@mui/material";
import type { PlatformRow, SearchGroup, TechStatus } from "../../types";
import { copy } from "../../copy";
import type { SearchGroupWrite } from "../../lib/inbox";
import { stripe } from "../../theme/palette";
import PlatformEnableList from "./PlatformEnableList";
import RunControls from "./RunControls";
import RunQueueSummary from "./RunQueueSummary";
import SearchGroupDrawer, {
  draftFromSearchGroup,
  emptyGroupDraft,
  parseGroupLines,
  type GroupDraft,
} from "./SearchGroupDrawer";
import SearchGroupList from "./SearchGroupList";
import TechDiagnostics from "./TechDiagnostics";

function Section({
  title,
  sticky,
  children,
}: {
  title?: string;
  sticky?: boolean;
  children: ReactNode;
}) {
  return (
    <Box
      sx={{
        pb: 2.5,
        mb: 0.5,
        borderBottom: `1px solid ${stripe.border}`,
        ...(sticky
          ? {
              position: "sticky",
              top: 0,
              zIndex: 2,
              bgcolor: "background.paper",
              pt: 0.5,
            }
          : {}),
      }}
    >
      {title ? (
        <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
          {title}
        </Typography>
      ) : null}
      {children}
    </Box>
  );
}

export default function TechRunPanel({
  status,
  groups,
  platforms,
  busy = false,
  error = null,
  groupError = null,
  onStart,
  onStop,
  onToggleQueue,
  onTogglePlatform,
  onSaveGroup,
  onDeleteGroup,
}: {
  status: TechStatus;
  groups: SearchGroup[];
  platforms: PlatformRow[];
  busy?: boolean;
  error?: string | null;
  groupError?: string | null;
  onStart: () => void;
  onStop: () => void;
  onToggleQueue: (group: SearchGroup, inQueue: boolean) => void;
  onTogglePlatform: (platform: PlatformRow, enabled: boolean) => void;
  onSaveGroup: (id: string | undefined, body: SearchGroupWrite) => Promise<void>;
  onDeleteGroup: (group: SearchGroup) => void;
}) {
  const [draft, setDraft] = useState<GroupDraft | null>(null);
  const [saving, setSaving] = useState(false);

  const queuedGroups = groups.filter((row) => row.in_queue).length;
  const enabledPlatforms = platforms.filter((row) => row.enabled).length;
  const locked = busy || status.running || saving;
  const canStart = !locked && queuedGroups > 0 && enabledPlatforms > 0;
  const canStop = !busy && status.running;
  const nextSort = groups.reduce((max, row) => Math.max(max, row.sort_order), -1) + 1;
  const showReport =
    !status.running && (status.phase === "done" || status.phase === "stopped" || status.phase === "partial");
  const diagnosticsForceOpen = status.phase === "error";

  const emptyPriority =
    groups.length === 0
      ? "groups"
      : enabledPlatforms === 0
        ? "platforms"
        : queuedGroups === 0
          ? "queued"
          : null;

  async function submitDraft() {
    if (!draft) return;
    const queries = parseGroupLines(draft.queriesText);
    if (!draft.name.trim() || queries.length === 0) return;
    setSaving(true);
    try {
      await onSaveGroup(draft.id, {
        name: draft.name.trim(),
        queries,
        exclude: parseGroupLines(draft.excludeText),
        limit_n: Math.max(0, Number(draft.limit_n) || 0),
        in_queue: draft.in_queue,
        sort_order: draft.sort_order,
      });
      setDraft(null);
    } catch {
      /* parent sets groupError */
    } finally {
      setSaving(false);
    }
  }

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2.5,
        border: `1px solid ${stripe.border}`,
        borderRadius: 1,
        maxWidth: 840,
      }}
    >
      <Stack spacing={0}>
        <Section title={copy.run_section_controls} sticky>
          <Stack spacing={1.5}>
            <RunControls
              canStart={canStart}
              canStop={canStop}
              busy={busy}
              running={status.running}
              onStart={onStart}
              onStop={onStop}
            />
            {error ? <Alert severity="error">{error}</Alert> : null}
            <RunQueueSummary
              status={status}
              queuedGroups={queuedGroups}
              enabledPlatforms={enabledPlatforms}
            />
            <Typography variant="body2" color="text.secondary">
              {status.running ? copy.run_running_hint : copy.run_idle_hint}
            </Typography>
            <Box>
              <Typography color="secondary" sx={{ fontWeight: 600 }}>
                {status.phase_label || copy.phase_idle}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {copy.progress_list
                  .replace("{n}", String(status.list_done))
                  .replace("{total}", String(status.list_total))}{" "}
                ·{" "}
                {copy.progress_cards
                  .replace("{k}", String(status.cards_done))
                  .replace("{total}", String(status.cards_total))}
                {status.http_retries > 0
                  ? ` · ${copy.http_retries_label}: ${status.http_retries}`
                  : ""}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">
                {copy.counters_legend}
              </Typography>
              <Stack direction="row" spacing={2} sx={{ mt: 0.5, alignItems: "baseline" }}>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  L1 {status.counters.L1}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  L2 {status.counters.L2}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  L3 {status.counters.L3}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  noise {status.counters.noise}
                </Typography>
              </Stack>
            </Box>
            {showReport ? (
              <Box>
                <Typography variant="caption" color="text.secondary">
                  {copy.run_report_legend}
                </Typography>
                <Stack spacing={0.25} sx={{ mt: 0.5 }}>
                  <Typography variant="body2">
                    {copy.run_report_new}: {status.run_report.new}
                  </Typography>
                  <Typography variant="body2">
                    {copy.run_report_already}: {status.run_report.already}
                  </Typography>
                  <Typography variant="body2">
                    {copy.run_report_updated}: {status.run_report.updated}
                  </Typography>
                  <Typography variant="body2">
                    {copy.run_report_expired}: {status.run_report.expired}
                  </Typography>
                </Stack>
                {status.ai_failures > 0 ? (
                  <Alert severity="warning" sx={{ mt: 1 }}>
                    {copy.ai_banner_failures.replace("{n}", String(status.ai_failures))}
                  </Alert>
                ) : null}
              </Box>
            ) : null}
          </Stack>
        </Section>

        <Section title={copy.run_section_groups}>
          {groupError ? <Alert severity="error" sx={{ mb: 1 }}>{groupError}</Alert> : null}
          {emptyPriority === "groups" ? null : emptyPriority === "queued" ? (
            <Alert severity="info" sx={{ mb: 1 }}>
              <Typography variant="body2">{copy.groups_none_queued}</Typography>
              <Typography variant="caption" display="block">
                {copy.groups_none_queued_body}
              </Typography>
            </Alert>
          ) : null}
          <SearchGroupList
            groups={groups}
            locked={locked}
            draftOpen={draft !== null}
            onAdd={() => setDraft(emptyGroupDraft(nextSort))}
            onEdit={(group) => setDraft(draftFromSearchGroup(group))}
            onDelete={onDeleteGroup}
            onToggleQueue={onToggleQueue}
          />
          {draft ? (
            <SearchGroupDrawer
              draft={draft}
              saving={saving}
              onChange={setDraft}
              onSave={() => void submitDraft()}
              onClose={() => setDraft(null)}
            />
          ) : null}
        </Section>

        <Section title={copy.run_section_platforms}>
          {emptyPriority === "platforms" ? (
            <Alert severity="info" sx={{ mb: 1 }}>
              <Typography variant="body2">{copy.platforms_none_enabled}</Typography>
              <Typography variant="caption" display="block">
                {copy.platforms_none_enabled_body}
              </Typography>
            </Alert>
          ) : null}
          <PlatformEnableList
            platforms={platforms}
            locked={locked}
            onToggle={onTogglePlatform}
          />
        </Section>

        <Box sx={{ pt: 2 }}>
          <TechDiagnostics status={status} forceOpen={diagnosticsForceOpen} />
        </Box>
      </Stack>
    </Paper>
  );
}

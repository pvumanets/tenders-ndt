import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  FormControlLabel,
  Paper,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import type { NamedSearch, QueueStepStatus, TechStatus } from "../../types";
import { copy } from "../../copy";
import {
  formatQueuePosition,
  platformLabel,
  queueStatusLabel,
  rostenderSessionCopy,
  type SearchWrite,
} from "../../lib/inbox";
import { stripe } from "../../theme/palette";
import SearchSettingsDrawer, {
  draftFromNamedSearch,
  emptySearchDraft,
  parseSearchQueries,
  type SearchDraft,
} from "./SearchSettingsDrawer";

export default function TechRunPanel({
  status,
  searches,
  busy = false,
  error = null,
  searchError = null,
  onStart,
  onStop,
  onToggleQueue,
  onSaveSearch,
  onDeleteSearch,
}: {
  status: TechStatus;
  searches: NamedSearch[];
  busy?: boolean;
  error?: string | null;
  searchError?: string | null;
  onStart: () => void;
  onStop: () => void;
  onToggleQueue: (search: NamedSearch, inQueue: boolean) => void;
  onSaveSearch: (id: string | undefined, body: SearchWrite) => Promise<void>;
  onDeleteSearch: (search: NamedSearch) => void;
}) {
  const [copied, setCopied] = useState(false);
  const [draft, setDraft] = useState<SearchDraft | null>(null);
  const [saving, setSaving] = useState(false);
  const queuedCount = searches.filter((row) => row.in_queue).length;
  const canEdit = !busy && !status.running && !saving;
  const canStart = canEdit && queuedCount > 0;
  const canStop = !busy && status.running;
  const nextSort = searches.reduce((max, row) => Math.max(max, row.sort_order), -1) + 1;
  const queueVisible = status.queue.length > 0;
  const queueCurrent = Math.min(status.queue_index + 1, Math.max(status.queue_total, status.queue.length));

  async function submitDraft() {
    if (!draft) return;
    const queries = parseSearchQueries(draft.queriesText);
    if (!draft.name.trim() || queries.length === 0) return;
    setSaving(true);
    try {
      await onSaveSearch(draft.id, {
        name: draft.name.trim(),
        platform_id: draft.platform_id,
        queries,
        limit_n: Math.min(1000, Math.max(1, Number(draft.limit_n) || 1)),
        in_queue: draft.in_queue,
        sort_order: draft.sort_order,
      });
      setDraft(null);
    } catch {
      /* parent sets searchError */
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
      <Stack spacing={2}>
        <Stack direction="row" spacing={1}>
          <Button variant="contained" disabled={!canStart} onClick={onStart}>
            {busy && !status.running ? copy.run_start_busy : copy.run_start}
          </Button>
          <Button variant="outlined" disabled={!canStop} onClick={onStop}>
            {copy.run_stop}
          </Button>
        </Stack>
        {error ? <Alert severity="error">{error}</Alert> : null}
        {!status.running && queuedCount === 0 ? (
          <Typography variant="body2" color="text.secondary">
            {copy.run_error_empty_queue}
          </Typography>
        ) : null}
        <Stack spacing={0.5}>
          <Typography variant="body2" color="primary" sx={{ fontWeight: 500 }}>
            {rostenderSessionCopy(status.session)}
          </Typography>
          <Typography variant="body2" color="primary" sx={{ fontWeight: 500 }}>
            {copy.session_tender_pro}
          </Typography>
        </Stack>
        {queueVisible ? (
          <Box>
            <Typography color="secondary" sx={{ fontWeight: 600 }}>
              {formatQueuePosition(queueCurrent, status.queue_total || status.queue.length)}
            </Typography>
            {status.current_search_name ? (
              <Typography variant="body2" color="text.secondary">
                {status.current_search_name}
              </Typography>
            ) : null}
            <Stack spacing={0.25} sx={{ mt: 0.5 }}>
              {status.queue.map((step) => (
                <Typography key={step.id} variant="body2">
                  {step.name} — {queueStatusLabel(step.status as QueueStepStatus)}
                </Typography>
              ))}
            </Stack>
          </Box>
        ) : null}
        <Box>
          <Typography color="secondary" sx={{ fontWeight: 600 }}>
            {status.phase_label || copy.phase_done}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Список: {status.list_done} / {status.list_total} · Карточки: {status.cards_done} /{" "}
            {status.cards_total}
          </Typography>
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary">
            {copy.counters_legend}
          </Typography>
          <Stack direction="row" spacing={2} sx={{ mt: 0.5 }}>
            <Typography variant="body2">L1 {status.counters.L1}</Typography>
            <Typography variant="body2">L2 {status.counters.L2}</Typography>
            <Typography variant="body2">L3 {status.counters.L3}</Typography>
            <Typography variant="body2">noise {status.counters.noise}</Typography>
          </Stack>
        </Box>
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

        <Box>
          <Stack direction="row" spacing={1} sx={{ mb: 1, alignItems: "center" }}>
            <Typography variant="subtitle2" sx={{ flex: 1 }}>
              {copy.searches_title}
            </Typography>
            <Button
              size="small"
              variant="outlined"
              disabled={!canEdit || draft !== null}
              onClick={() => setDraft(emptySearchDraft(nextSort))}
            >
              {copy.searches_add}
            </Button>
          </Stack>
          {searchError ? <Alert severity="error" sx={{ mb: 1 }}>{searchError}</Alert> : null}
          {searches.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              {copy.searches_empty}
            </Typography>
          ) : (
            <Stack spacing={1}>
              {searches.map((search) => (
                <Box
                  key={search.id}
                  sx={{
                    py: 0.75,
                    px: 0.5,
                    borderBottom: `1px solid ${stripe.border}`,
                  }}
                >
                  <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                    <Typography sx={{ flex: 1, minWidth: 0 }} noWrap>
                      {search.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ flexShrink: 0 }}>
                      {platformLabel(search.platform_id)}
                    </Typography>
                    <FormControlLabel
                      sx={{ mr: 0, flexShrink: 0 }}
                      control={
                        <Switch
                          size="small"
                          checked={search.in_queue}
                          disabled={!canEdit}
                          onChange={(_, checked) => onToggleQueue(search, checked)}
                          slotProps={{ input: { "aria-label": `${copy.searches_queue}: ${search.name}` } }}
                        />
                      }
                      label={copy.searches_queue}
                    />
                    <Button
                      size="small"
                      disabled={!canEdit}
                      onClick={() => setDraft(draftFromNamedSearch(search))}
                    >
                      {copy.searches_edit}
                    </Button>
                    <Button
                      size="small"
                      color="error"
                      disabled={!canEdit}
                      onClick={() => {
                        if (window.confirm(copy.searches_delete_confirm)) onDeleteSearch(search);
                      }}
                    >
                      {copy.searches_delete}
                    </Button>
                  </Stack>
                  <Typography variant="caption" color="text.secondary">
                    {search.queries.join(", ")} · {copy.searches_limit} {search.limit_n}
                  </Typography>
                  {search.platform_id === "tender-pro" ? (
                    <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                      {copy.searches_tender_pro_docs}
                    </Typography>
                  ) : null}
                </Box>
              ))}
            </Stack>
          )}
          {draft ? (
            <SearchSettingsDrawer
              draft={draft}
              saving={saving}
              onChange={setDraft}
              onSave={() => void submitDraft()}
              onClose={() => setDraft(null)}
            />
          ) : null}
        </Box>

        <Box>
          <Typography variant="caption" color="text.secondary">
            {copy.run_path_label}
          </Typography>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ mt: 0.5 }}>
            <TextField
              size="small"
              fullWidth
              value={status.run_dir}
              slotProps={{ input: { readOnly: true } }}
            />
            <Button
              size="small"
              variant="outlined"
              sx={{ alignSelf: { xs: "flex-start", sm: "center" }, flexShrink: 0 }}
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(status.run_dir);
                  setCopied(true);
                  window.setTimeout(() => setCopied(false), 1500);
                } catch {
                  /* ignore */
                }
              }}
            >
              {copied ? copy.run_path_copied : copy.run_path_copy}
            </Button>
          </Stack>
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary">
            {copy.log_title}
          </Typography>
          <Box
            component="ul"
            sx={{
              m: 0,
              mt: 0.5,
              p: 1.5,
              listStyle: "none",
              bgcolor: stripe.surfaceSubtle,
              border: `1px solid ${stripe.border}`,
              borderRadius: 1,
              fontFamily: "ui-monospace, Consolas, monospace",
              fontSize: 12,
              maxHeight: 220,
              overflow: "auto",
            }}
          >
            {status.log.length === 0 ? (
              <li>{copy.log_empty}</li>
            ) : (
              status.log.map((line, i) => (
                <li
                  key={`${line.t}-${i}`}
                  style={{ color: line.level === "error" ? stripe.critical : undefined }}
                >
                  {line.t} {line.msg}
                </li>
              ))
            )}
          </Box>
        </Box>
      </Stack>
    </Paper>
  );
}

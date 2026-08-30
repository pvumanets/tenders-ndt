import { Alert, Box, Stack, Typography } from "@mui/material";
import type { TechStatus } from "../../types";
import { copy } from "../../copy";
import RunControls from "./RunControls";
import RunQueueSummary from "./RunQueueSummary";
import { stripe } from "../../theme/palette";

export default function ManualRunControls({
  status,
  queuedGroups,
  enabledPlatforms,
  busy = false,
  error = null,
  onStart,
  onStop,
}: {
  status: TechStatus;
  queuedGroups: number;
  enabledPlatforms: number;
  busy?: boolean;
  error?: string | null;
  onStart: () => void;
  onStop: () => void;
}) {
  const locked = busy || status.running;
  const canStart = !locked && queuedGroups > 0 && enabledPlatforms > 0;
  const canStop = !busy && status.running;
  const showReport =
    !status.running &&
    (status.phase === "done" ||
      status.phase === "stopped" ||
      status.phase === "partial" ||
      status.phase === "error");

  return (
    <Box
      sx={{
        position: "sticky",
        top: 0,
        zIndex: 2,
        bgcolor: "background.paper",
        pb: 2,
        mb: 1.5,
        borderBottom: `1px solid ${stripe.border}`,
      }}
    >
      <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
        {copy.run_section_controls}
      </Typography>
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
        {!status.running && (queuedGroups === 0 || enabledPlatforms === 0) ? (
          <Typography variant="body2" sx={{ color: stripe.textMuted }}>
            {copy.empty_manual_queue}
          </Typography>
        ) : null}
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
            {status.http_retries > 0 ? ` · ${copy.http_retries_label}: ${status.http_retries}` : ""}
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
    </Box>
  );
}

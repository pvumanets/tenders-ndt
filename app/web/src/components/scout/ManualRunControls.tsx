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
  const progressLine = [
    copy.progress_list
      .replace("{n}", String(status.list_done))
      .replace("{total}", String(status.list_total)),
    copy.progress_cards
      .replace("{k}", String(status.cards_done))
      .replace("{total}", String(status.cards_total)),
    status.http_retries > 0 ? `${copy.http_retries_label}: ${status.http_retries}` : null,
  ]
    .filter(Boolean)
    .join(" · ");
  const countersLine = `L1 ${status.counters.L1} · L2 ${status.counters.L2} · L3 ${status.counters.L3} · noise ${status.counters.noise}`;

  return (
    <Box
      sx={{
        mb: 1,
        pb: 1,
        borderBottom: `1px solid ${stripe.border}`,
      }}
    >
      <Typography variant="subtitle2" sx={{ mb: 0.75 }}>
        {copy.run_section_controls}
      </Typography>
      <Stack spacing={0.75}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1}
          sx={{ alignItems: { sm: "flex-start" } }}
        >
          <RunControls
            canStart={canStart}
            canStop={canStop}
            busy={busy}
            running={status.running}
            onStart={onStart}
            onStop={onStop}
          />
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <RunQueueSummary
              status={status}
              queuedGroups={queuedGroups}
              enabledPlatforms={enabledPlatforms}
            />
            <Typography variant="body2" color="secondary" sx={{ fontWeight: 600 }}>
              {status.phase_label || copy.phase_idle}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
              {progressLine}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
              {status.running ? copy.run_running_hint : copy.run_idle_hint}
            </Typography>
          </Box>
        </Stack>
        {error ? <Alert severity="error">{error}</Alert> : null}
        {!status.running && (queuedGroups === 0 || enabledPlatforms === 0) ? (
          <Typography variant="body2" sx={{ color: stripe.textMuted }}>
            {copy.empty_manual_queue}
          </Typography>
        ) : null}
        <Typography variant="caption" color="text.secondary">
          {copy.counters_legend}: {countersLine}
        </Typography>
        {showReport ? (
          <Box>
            <Typography variant="caption" color="text.secondary">
              {copy.run_report_legend}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
              {copy.run_report_new}: {status.run_report.new}
              {" · "}
              {copy.run_report_already}: {status.run_report.already}
              {" · "}
              {copy.run_report_updated}: {status.run_report.updated}
              {" · "}
              {copy.run_report_expired}: {status.run_report.expired}
            </Typography>
            {status.ai_failures > 0 ? (
              <Alert severity="warning" sx={{ mt: 0.75, py: 0 }}>
                {copy.ai_banner_failures.replace("{n}", String(status.ai_failures))}
              </Alert>
            ) : null}
          </Box>
        ) : null}
      </Stack>
    </Box>
  );
}

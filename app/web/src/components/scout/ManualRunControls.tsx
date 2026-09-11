import { Alert, Box, Chip, Stack, Typography } from "@mui/material";
import type { TechStatus } from "../../types";
import { copy } from "../../copy";
import RunControls from "./RunControls";
import {
  formatQueueStepLine,
  formatQueueSummary,
  platformLabel,
} from "../../lib/inbox";
import { stripe } from "../../theme/palette";

function runChipLabel(status: TechStatus): string {
  if (status.running) return copy.run_chip_running;
  switch (status.phase) {
    case "done":
      return copy.run_chip_done;
    case "partial":
      return copy.run_chip_partial;
    case "stopped":
      return copy.run_chip_stopped;
    case "error":
      return copy.run_chip_error;
    default:
      return copy.run_chip_idle;
  }
}

function runChipColors(status: TechStatus): { bg: string; fg: string } {
  if (status.running) return { bg: stripe.infoSoft, fg: stripe.info };
  if (status.phase === "done") return { bg: stripe.successSoft, fg: stripe.success };
  if (status.phase === "error") return { bg: stripe.criticalSoft, fg: stripe.critical };
  if (status.phase === "partial" || status.phase === "stopped") {
    return { bg: stripe.warningSoft, fg: stripe.warning };
  }
  return { bg: "rgba(105, 115, 134, 0.12)", fg: stripe.textMuted };
}

function ProgressMetric({ label, value }: { label: string; value: string }) {
  return (
    <Box sx={{ minWidth: 0 }}>
      <Typography variant="caption" sx={{ color: stripe.textMuted, display: "block", lineHeight: 1.2 }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 600, color: stripe.navy, lineHeight: 1.3 }}>
        {value}
      </Typography>
    </Box>
  );
}

function TierPill({ label, value }: { label: string; value: number }) {
  return (
    <Box
      component="span"
      sx={{
        display: "inline-flex",
        alignItems: "center",
        height: 20,
        px: 0.75,
        borderRadius: 1,
        bgcolor: stripe.surface,
        border: `1px solid ${stripe.border}`,
        fontSize: 11,
        lineHeight: 1,
        color: stripe.text,
        gap: 0.5,
      }}
    >
      <Box component="span" sx={{ color: stripe.textMuted }}>
        {label}
      </Box>
      <Box component="span" sx={{ fontWeight: 600 }}>
        {value}
      </Box>
    </Box>
  );
}

function queueCaption(
  status: TechStatus,
  queuedGroups: number,
  enabledPlatforms: number,
): string {
  if (status.running && status.queue_total > 0) {
    const current = Math.min(
      status.queue_index + 1,
      Math.max(status.queue_total, status.queue.length),
    );
    const step = status.queue[status.queue_index];
    const group = step?.group_name || step?.name || status.current_search_name || "—";
    const platform = platformLabel(step?.platform_id || status.current_platform_id || "");
    return formatQueueStepLine(current, status.queue_total, group, platform);
  }
  const steps = queuedGroups * enabledPlatforms;
  if (steps === 0) return copy.run_queue_empty;
  return formatQueueSummary(queuedGroups, enabledPlatforms, steps);
}

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
  const showDetails = status.running || showReport;
  const chip = runChipColors(status);
  const queueEmpty = !status.running && (queuedGroups === 0 || enabledPlatforms === 0);

  return (
    <Box
      sx={{
        mb: 1,
        pb: 1.5,
        borderBottom: `1px solid ${stripe.border}`,
      }}
    >
      <Stack spacing={1}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          sx={{ alignItems: { sm: "flex-start" } }}
        >
          <Box sx={{ flexShrink: 0, pt: 0.25 }}>
            <RunControls
              canStart={canStart}
              canStop={canStop}
              busy={busy}
              running={status.running}
              onStart={onStart}
              onStop={onStop}
            />
          </Box>

          <Box
            sx={{
              flex: 1,
              minWidth: 0,
              bgcolor: stripe.surfaceSubtle,
              border: `1px solid ${stripe.border}`,
              borderRadius: 1,
              px: 1.25,
              py: 1,
            }}
          >
            <Chip
              size="small"
              label={runChipLabel(status)}
              sx={{
                height: 22,
                mb: 0.75,
                bgcolor: chip.bg,
                color: chip.fg,
                fontWeight: 600,
                borderRadius: 1,
              }}
            />
            <Typography variant="caption" sx={{ color: stripe.textMuted, display: "block" }}>
              {queueCaption(status, queuedGroups, enabledPlatforms)}
            </Typography>

            {showDetails ? (
              <>
                <Stack direction="row" spacing={3} sx={{ mt: 1.25 }}>
                  <ProgressMetric
                    label={copy.progress_list_label}
                    value={`${status.list_done}/${status.list_total}`}
                  />
                  <ProgressMetric
                    label={copy.progress_cards_label}
                    value={`${status.cards_done}/${status.cards_total}`}
                  />
                  {status.http_retries > 0 ? (
                    <ProgressMetric
                      label={copy.http_retries_label}
                      value={String(status.http_retries)}
                    />
                  ) : null}
                </Stack>
                <Stack direction="row" sx={{ mt: 1, flexWrap: "wrap", gap: 0.75 }}>
                  <TierPill label={copy.tier_label_l1} value={status.counters.L1} />
                  <TierPill label={copy.tier_label_l2} value={status.counters.L2} />
                  <TierPill label={copy.tier_label_l3} value={status.counters.L3} />
                  <TierPill label={copy.tier_label_noise} value={status.counters.noise} />
                </Stack>
              </>
            ) : null}
          </Box>
        </Stack>

        {error ? <Alert severity="error">{error}</Alert> : null}
        {queueEmpty ? (
          <Typography variant="body2" sx={{ color: stripe.textMuted }}>
            {copy.empty_manual_queue}
          </Typography>
        ) : null}
        {status.running ? (
          <Typography variant="caption" sx={{ color: stripe.textMuted }}>
            {copy.run_running_hint}
          </Typography>
        ) : null}
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

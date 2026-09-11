import { Box, Button, Stack, Typography } from "@mui/material";
import { labCopy as t } from "../labCopy";
import type { LabMockState } from "../labMocks";
import { stripe } from "../../theme/palette";

function shiftStatus(state: LabMockState): string {
  if (state.ai === "busy") {
    return t.b_status_ai.replace("{pending}", String(state.pendingAi));
  }
  if (state.ai === "done") return t.b_status_ai_done;
  if (state.phase === "running") {
    return t.b_status_running
      .replace("{n}", String(state.listDone))
      .replace("{total}", String(state.listTotal));
  }
  if (state.phase === "done") {
    return t.b_status_done.replace("{pending}", String(state.pendingAi));
  }
  return t.b_status_idle.replace("{steps}", String(state.steps));
}

export default function RunChromeVariantB({
  state,
  onPrimary,
  onOnlyRun,
  onOnlyAi,
  onStop,
}: {
  state: LabMockState;
  onPrimary: () => void;
  onOnlyRun: () => void;
  onOnlyAi: () => void;
  onStop: () => void;
}) {
  const busy = state.phase === "running" || state.ai === "busy";
  const showOutcome = state.ai === "done" || (state.phase === "done" && state.ai === "idle");
  const counters = t.b_counters
    .replace("{l1}", String(state.counters.L1))
    .replace("{l2}", String(state.counters.L2))
    .replace("{l3}", String(state.counters.L3));

  return (
    <Box
      sx={{
        border: `1px solid ${stripe.border}`,
        borderRadius: 1.5,
        bgcolor: stripe.surface,
        p: 2,
      }}
    >
      <Typography variant="caption" sx={{ color: stripe.textMuted, display: "block", mb: 0.75 }}>
        {t.b_slot.replace("{when}", state.slotWhen)}
      </Typography>

      <Typography variant="subtitle1" sx={{ fontWeight: 600, color: stripe.navy, mb: 1.5 }}>
        {shiftStatus(state)}
      </Typography>

      <Stack spacing={1.25}>
        <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", alignItems: "center" }}>
          <Button
            variant="contained"
            size="medium"
            disabled={busy}
            onClick={onPrimary}
            sx={{ bgcolor: stripe.blurple, px: 2 }}
          >
            {busy ? t.b_primary_busy : t.b_primary}
          </Button>
          {busy ? (
            <Button variant="outlined" size="small" onClick={onStop}>
              {t.b_stop}
            </Button>
          ) : null}
        </Stack>
        {!busy ? (
          <Typography variant="body2" sx={{ color: stripe.textMuted }}>
            {t.b_primary_hint}
          </Typography>
        ) : null}

        <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
          <Button variant="outlined" size="small" disabled={busy} onClick={onOnlyRun}>
            {t.b_only_run}
          </Button>
          <Button
            variant="outlined"
            size="small"
            disabled={busy || state.phase === "idle"}
            onClick={onOnlyAi}
          >
            {t.b_only_ai}
          </Button>
        </Stack>

        {(state.phase !== "idle" || state.ai !== "idle") && (
          <Typography variant="caption" sx={{ color: stripe.textMuted }}>
            {counters}
          </Typography>
        )}

        {showOutcome ? (
          <Box
            sx={{
              mt: 0.5,
              px: 1.25,
              py: 1,
              borderRadius: 1,
              bgcolor: stripe.successSoft,
              color: stripe.success,
            }}
          >
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {t.b_outcome}
            </Typography>
          </Box>
        ) : null}
      </Stack>
    </Box>
  );
}

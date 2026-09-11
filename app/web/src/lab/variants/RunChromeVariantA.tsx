import { Box, Button, Chip, Stack, Typography } from "@mui/material";
import { labCopy as t } from "../labCopy";
import type { LabMockState } from "../labMocks";
import { stripe } from "../../theme/palette";

function statusLabel(state: LabMockState): string {
  if (state.phase === "running") return t.a_status_running;
  if (state.phase === "done") return t.a_status_done;
  return t.a_status_idle;
}

function statusColor(state: LabMockState): { bg: string; fg: string } {
  if (state.phase === "running") return { bg: stripe.infoSoft, fg: stripe.info };
  if (state.phase === "done") return { bg: stripe.successSoft, fg: stripe.success };
  return { bg: stripe.surfaceSubtle, fg: stripe.textMuted };
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

export default function RunChromeVariantA({
  state,
  onStart,
  onStop,
  onAi,
}: {
  state: LabMockState;
  onStart: () => void;
  onStop: () => void;
  onAi: () => void;
}) {
  const running = state.phase === "running";
  const showDetails = running || state.phase === "done";
  const chip = statusColor(state);
  const queue = t.a_queue
    .replace("{groups}", String(state.groups))
    .replace("{platforms}", String(state.platforms))
    .replace("{steps}", String(state.steps));

  return (
    <Box
      sx={{
        border: `1px solid ${stripe.border}`,
        borderRadius: 1.5,
        bgcolor: stripe.surface,
        p: 2,
      }}
    >
      <Typography variant="caption" sx={{ color: stripe.textMuted, display: "block", mb: 1.5 }}>
        {t.a_slot.replace("{when}", state.slotWhen)}
      </Typography>

      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        sx={{ alignItems: { sm: "flex-start" }, mb: 2 }}
      >
        <Stack direction="row" spacing={1} sx={{ flexShrink: 0, pt: 0.25 }}>
          <Button
            variant="contained"
            size="small"
            disabled={running || state.ai === "busy"}
            onClick={onStart}
            sx={{ bgcolor: stripe.blurple }}
          >
            {t.a_run_start}
          </Button>
          <Button variant="outlined" size="small" disabled={!running} onClick={onStop}>
            {t.a_run_stop}
          </Button>
        </Stack>

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
            label={statusLabel(state)}
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
            {queue}
          </Typography>

          {showDetails ? (
            <>
              <Stack direction="row" spacing={3} sx={{ mt: 1.25 }}>
                <ProgressMetric
                  label={t.a_progress_list}
                  value={`${state.listDone}/${state.listTotal}`}
                />
                <ProgressMetric
                  label={t.a_progress_cards}
                  value={`${state.cardsDone}/${state.cardsTotal}`}
                />
              </Stack>
              <Stack direction="row" sx={{ mt: 1, flexWrap: "wrap", gap: 0.75 }}>
                <TierPill label={t.a_tier_l1} value={state.counters.L1} />
                <TierPill label={t.a_tier_l2} value={state.counters.L2} />
                <TierPill label={t.a_tier_l3} value={state.counters.L3} />
                <TierPill label={t.a_tier_noise} value={state.counters.noise} />
              </Stack>
            </>
          ) : null}
        </Box>
      </Stack>

      <Box
        sx={{
          pt: 1.5,
          borderTop: `1px solid ${stripe.border}`,
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: 1.5,
        }}
      >
        <Button
          variant="outlined"
          size="small"
          disabled={running || state.ai === "busy" || state.phase === "idle"}
          onClick={onAi}
        >
          {state.ai === "busy" ? t.a_ai_busy : t.a_ai}
        </Button>
        <Typography variant="body2" sx={{ color: stripe.textMuted }}>
          {t.a_ai_hint}
        </Typography>
      </Box>
      <Typography variant="caption" sx={{ color: stripe.textMuted, display: "block", mt: 1 }}>
        {t.a_bitrix}
      </Typography>
    </Box>
  );
}

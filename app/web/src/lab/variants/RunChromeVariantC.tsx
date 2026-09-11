import { Box, Button, Stack, Typography } from "@mui/material";
import { labCopy as t } from "../labCopy";
import type { LabMockState } from "../labMocks";
import { stripe } from "../../theme/palette";

type QueueItem = {
  id: "run" | "ai" | "manual";
  done: boolean;
  label: string;
  hint?: string;
};

function buildQueue(state: LabMockState): QueueItem[] {
  const aiDone = state.ai === "done" || (state.phase === "done" && state.pendingAi === 0);
  const runLabel =
    state.phase === "done"
      ? t.c_item_run_done
      : state.phase === "running"
        ? `${t.c_item_run
            .replace("{groups}", String(state.groups))
            .replace("{platforms}", String(state.platforms))} · идёт`
        : t.c_item_run
            .replace("{groups}", String(state.groups))
            .replace("{platforms}", String(state.platforms));
  return [
    {
      id: "run",
      done: state.phase === "done",
      label: runLabel,
    },
    {
      id: "ai",
      done: aiDone,
      label: aiDone ? t.c_item_ai_done : t.c_item_ai.replace("{n}", String(state.pendingAi)),
    },
    {
      id: "manual",
      done: state.manualSend === 0,
      label: t.c_item_manual.replace("{n}", String(state.manualSend)),
      hint: t.c_item_manual_hint,
    },
  ];
}

function primaryFor(queue: QueueItem[]): { label: string; action: "run" | "ai" | "manual" } {
  const open = queue.find((q) => !q.done);
  if (!open || open.id === "run") return { label: t.c_cta_run, action: "run" };
  if (open.id === "ai") return { label: t.c_cta_ai, action: "ai" };
  return { label: t.c_cta_manual, action: "manual" };
}

export default function RunChromeVariantC({
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
  const queue = buildQueue(state);
  const primary = primaryFor(queue);
  const running = state.phase === "running";
  const busy = running || state.ai === "busy";
  const summary = t.c_summary
    .replace("{l1}", String(state.counters.L1))
    .replace("{l2}", String(state.counters.L2))
    .replace("{l3}", String(state.counters.L3))
    .replace("{noise}", String(state.counters.noise));

  return (
    <Box
      sx={{
        border: `1px solid ${stripe.border}`,
        borderRadius: 1.5,
        bgcolor: stripe.surface,
        p: 2,
      }}
    >
      <Typography variant="subtitle2" sx={{ mb: 1.25, color: stripe.navy }}>
        {t.c_now}
      </Typography>

      <Stack spacing={0} sx={{ mb: 2 }}>
        {queue.map((item, idx) => {
          const isNext = !item.done && queue.slice(0, idx).every((q) => q.done);
          return (
            <Box
              key={item.id}
              sx={{
                py: 1,
                px: 1.25,
                borderRadius: 1,
                bgcolor: isNext ? stripe.blurpleSoft : "transparent",
                borderLeft: `3px solid ${item.done ? stripe.success : isNext ? stripe.blurple : stripe.border}`,
                mb: 0.5,
              }}
            >
              <Typography
                variant="body2"
                sx={{
                  fontWeight: isNext ? 600 : 400,
                  color: item.done ? stripe.textMuted : stripe.text,
                  textDecoration: item.done ? "line-through" : "none",
                }}
              >
                {item.label}
              </Typography>
              {item.hint && isNext ? (
                <Typography variant="caption" sx={{ color: stripe.textMuted, display: "block" }}>
                  {item.hint}
                </Typography>
              ) : null}
            </Box>
          );
        })}
      </Stack>

      <Stack direction="row" spacing={1} sx={{ mb: 1.5, flexWrap: "wrap" }}>
        <Button
          variant="contained"
          size="small"
          disabled={busy || primary.action === "manual"}
          onClick={() => {
            if (primary.action === "run") onStart();
            else if (primary.action === "ai") onAi();
          }}
          sx={{ bgcolor: stripe.blurple }}
        >
          {state.ai === "busy" ? t.a_ai_busy : running ? "Прогон…" : primary.label}
        </Button>
        {running ? (
          <Button variant="outlined" size="small" onClick={onStop}>
            {t.c_stop}
          </Button>
        ) : null}
      </Stack>

      <Stack
        direction="row"
        spacing={2}
        sx={{
          pt: 1.25,
          borderTop: `1px solid ${stripe.border}`,
          flexWrap: "wrap",
        }}
      >
        <Typography variant="caption" sx={{ color: stripe.textMuted }}>
          {t.c_slot.replace("{when}", state.slotWhen)}
        </Typography>
        <Typography variant="caption" sx={{ color: stripe.textMuted }}>
          {summary}
        </Typography>
      </Stack>
    </Box>
  );
}

import { useState } from "react";
import { Alert, Box, Button, Paper, Stack, TextField, Typography } from "@mui/material";
import type { TechStatus } from "../../types";
import { copy } from "../../copy";
import { stripe } from "../../theme/palette";

export default function TechRunPanel({
  status,
  busy = false,
  error = null,
  onStart,
  onStop,
}: {
  status: TechStatus;
  busy?: boolean;
  error?: string | null;
  onStart: () => void;
  onStop: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const sessionLabel =
    status.session === "ok"
      ? copy.session_ok
      : status.session === "expired"
        ? copy.session_expired
        : copy.session_missing;
  const canStart = !busy && !status.running && status.session === "ok";
  const canStop = !busy && status.running;

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
        {error ? (
          <Alert severity="error">{error}</Alert>
        ) : null}
        <Typography variant="body2" color="primary" sx={{ fontWeight: 500 }}>
          {sessionLabel}
        </Typography>
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

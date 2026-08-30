import { useEffect, useState } from "react";
import { Alert, Box, Button, FormControlLabel, Stack, Switch, TextField, Typography } from "@mui/material";
import { copy } from "../../copy";
import type { ScheduleSettings, TechStatus } from "../../types";
import { putSchedule } from "../../lib/inbox";
import { slotStatusText, slotVariant } from "../../lib/slot-status";
import { stripe } from "../../theme/palette";

export default function SettingsSchedule({
  schedule,
  status,
  locked,
  onSaved,
}: {
  schedule: ScheduleSettings;
  status: TechStatus;
  locked: boolean;
  onSaved: (next: ScheduleSettings) => void;
}) {
  const [enabled, setEnabled] = useState(schedule.enabled);
  const [timeMsk, setTimeMsk] = useState(schedule.time_msk);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setEnabled(schedule.enabled);
    setTimeMsk(schedule.time_msk);
  }, [schedule.enabled, schedule.time_msk]);

  const variant = slotVariant(schedule, status);
  const muted =
    variant === "skipped_already_running" || variant === "skipped_empty_queue" || variant === "last"
      ? slotStatusText(schedule, status)
      : !enabled
        ? copy.schedule_disabled_hint
        : slotStatusText(schedule, status);

  async function onSave() {
    setError(null);
    setSaved(false);
    if (!/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(timeMsk.trim())) {
      setError(copy.schedule_invalid_time);
      return;
    }
    setBusy(true);
    try {
      const next = await putSchedule({ enabled, time_msk: timeMsk.trim() });
      onSaved(next);
      setSaved(true);
    } catch (err: unknown) {
      setError(err instanceof Error && err.message === "invalid_time_msk" ? copy.schedule_invalid_time : copy.schedule_invalid_time);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Stack spacing={1.5}>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ alignItems: { sm: "center" } }}>
        <FormControlLabel
          control={
            <Switch
              checked={enabled}
              disabled={locked || busy}
              onChange={(_, checked) => {
                setEnabled(checked);
                setSaved(false);
              }}
            />
          }
          label={copy.schedule_enabled}
        />
        <TextField
          size="small"
          type="time"
          label={copy.schedule_time}
          value={timeMsk}
          disabled={locked || busy}
          onChange={(e) => {
            setTimeMsk(e.target.value);
            setSaved(false);
          }}
          slotProps={{ inputLabel: { shrink: true } }}
        />
        <Button variant="contained" size="small" disabled={locked || busy} onClick={() => void onSave()}>
          {copy.schedule_save}
        </Button>
      </Stack>
      <Typography variant="body2" sx={{ color: stripe.textMuted }}>
        {muted}
      </Typography>
      {error ? <Alert severity="error">{error}</Alert> : null}
      {saved ? (
        <Box>
          <Alert severity="success">{copy.schedule_saved}</Alert>
        </Box>
      ) : null}
    </Stack>
  );
}

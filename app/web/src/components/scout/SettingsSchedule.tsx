import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  FormControlLabel,
  Stack,
  Switch,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { copy } from "../../copy";
import type { ScheduleSettings, TechStatus } from "../../types";
import { putSchedule } from "../../lib/inbox";
import { slotStatusText, slotVariant } from "../../lib/slot-status";
import { stripe } from "../../theme/palette";

const WEEKDAY_OPTIONS: { id: number; label: string }[] = [
  { id: 0, label: copy.schedule_day_mon },
  { id: 1, label: copy.schedule_day_tue },
  { id: 2, label: copy.schedule_day_wed },
  { id: 3, label: copy.schedule_day_thu },
  { id: 4, label: copy.schedule_day_fri },
  { id: 5, label: copy.schedule_day_sat },
  { id: 6, label: copy.schedule_day_sun },
];

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
  const [weekdays, setWeekdays] = useState<number[]>(schedule.weekdays);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setEnabled(schedule.enabled);
    setTimeMsk(schedule.time_msk);
    setWeekdays(schedule.weekdays);
  }, [schedule.enabled, schedule.time_msk, schedule.weekdays]);

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
    if (weekdays.length === 0) {
      setError(copy.schedule_invalid_weekdays);
      return;
    }
    setBusy(true);
    try {
      const next = await putSchedule({
        enabled,
        time_msk: timeMsk.trim(),
        weekdays,
      });
      onSaved(next);
      setSaved(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      setError(
        msg === "invalid_time_msk"
          ? copy.schedule_invalid_time
          : msg === "invalid_weekdays"
            ? copy.schedule_invalid_weekdays
            : copy.schedule_save_failed,
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Stack spacing={1.75}>
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

      <Box>
        <Typography
          variant="caption"
          sx={{
            display: "block",
            mb: 0.75,
            color: stripe.textMuted,
            fontWeight: 600,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
          }}
        >
          {copy.schedule_weekdays}
        </Typography>
        <ToggleButtonGroup
          exclusive={false}
          size="small"
          value={weekdays}
          disabled={locked || busy}
          onChange={(_, next: number[]) => {
            setWeekdays([...next].sort((a, b) => a - b));
            setSaved(false);
          }}
          sx={{
            flexWrap: "wrap",
            gap: 0.75,
            "& .MuiToggleButtonGroup-grouped": {
              border: `1px solid ${stripe.border} !important`,
              borderRadius: "10px !important",
              margin: 0,
              px: 1.25,
              minWidth: 44,
              color: stripe.navy,
              bgcolor: stripe.surface,
              "&.Mui-selected": {
                bgcolor: stripe.blurpleSoft,
                color: stripe.blurple,
                borderColor: `${stripe.blurple} !important`,
                fontWeight: 600,
                "&:hover": { bgcolor: stripe.blurpleSoft },
              },
            },
          }}
        >
          {WEEKDAY_OPTIONS.map((opt) => (
            <ToggleButton key={opt.id} value={opt.id} aria-label={opt.label}>
              {opt.label}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
        <Typography variant="caption" sx={{ display: "block", mt: 0.75, color: stripe.textMuted }}>
          {copy.schedule_weekdays_hint}
        </Typography>
      </Box>

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

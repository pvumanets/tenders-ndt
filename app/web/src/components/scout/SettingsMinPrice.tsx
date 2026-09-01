import { useEffect, useState } from "react";
import { Alert, Box, Button, Slider, Stack, Typography } from "@mui/material";
import { copy } from "../../copy";
import type { OperatorSettings } from "../../types";
import { putOperatorSettings } from "../../lib/inbox";
import { formatPrice } from "../../lib/format";
import { stripe } from "../../theme/palette";

const MIN_PRICE_MAX = 5_000_000;

function minPriceStep(value: number): number {
  if (value <= 100_000) return 10_000;
  if (value <= 500_000) return 5_000;
  return 50_000;
}

function snapMinPrice(value: number): number {
  if (!Number.isFinite(value)) return 0;
  const clamped = Math.max(0, Math.min(MIN_PRICE_MAX, value));
  const step = minPriceStep(clamped);
  return Math.round(clamped / step) * step;
}

function normalizeMinPrice(value: unknown): number {
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) return 100_000;
  return snapMinPrice(n);
}

export default function SettingsMinPrice({
  settings,
  locked,
  onSaved,
}: {
  settings: OperatorSettings;
  locked: boolean;
  onSaved: (next: OperatorSettings) => void;
}) {
  const [value, setValue] = useState(() => normalizeMinPrice(settings.l1_min_price_rub));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setValue(normalizeMinPrice(settings.l1_min_price_rub));
  }, [settings.l1_min_price_rub]);

  async function onSave() {
    setError(null);
    setSaved(false);
    const snapped = snapMinPrice(value);
    setValue(snapped);
    setBusy(true);
    try {
      const next = await putOperatorSettings({ l1_min_price_rub: snapped });
      onSaved(next);
      setSaved(true);
    } catch (err: unknown) {
      setError(
        err instanceof Error && err.message === "invalid_l1_min_price_rub"
          ? copy.min_price_invalid
          : copy.min_price_save_failed,
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Stack spacing={1.5}>
      <Typography variant="body2" sx={{ color: stripe.textMuted }}>
        {copy.min_price_hint}
      </Typography>
      <Typography variant="body1" sx={{ fontWeight: 600 }}>
        {copy.min_price_value.replace("{price}", formatPrice(value))}
      </Typography>
      <Box sx={{ width: "100%", maxWidth: 520, pt: 0.5, pb: 0.25 }}>
        <Slider
          value={value}
          min={0}
          max={MIN_PRICE_MAX}
          step={1_000}
          disabled={locked || busy}
          onChange={(_, next) => {
            const raw = typeof next === "number" ? next : next[0];
            setValue(snapMinPrice(raw));
            setSaved(false);
          }}
          valueLabelDisplay="auto"
          valueLabelFormat={(v) => formatPrice(v)}
          sx={{
            mt: 0.5,
            mb: 0.5,
            "& .MuiSlider-thumb": { width: 18, height: 18 },
          }}
        />
        <Stack direction="row" sx={{ px: 0.5, justifyContent: "space-between" }}>
          <Typography variant="caption" sx={{ color: stripe.textMuted }}>
            0 ₽
          </Typography>
          <Typography variant="caption" sx={{ color: stripe.textMuted }}>
            {formatPrice(MIN_PRICE_MAX)}
          </Typography>
        </Stack>
      </Box>
      <Box sx={{ pt: 0.5 }}>
        <Button variant="contained" size="small" disabled={locked || busy} onClick={() => void onSave()}>
          {copy.min_price_save}
        </Button>
      </Box>
      {error ? <Alert severity="error">{error}</Alert> : null}
      {saved ? <Alert severity="success">{copy.min_price_saved}</Alert> : null}
    </Stack>
  );
}

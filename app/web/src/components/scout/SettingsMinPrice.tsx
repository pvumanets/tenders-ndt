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
  const clamped = Math.max(0, Math.min(MIN_PRICE_MAX, value));
  const step = minPriceStep(clamped);
  return Math.round(clamped / step) * step;
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
  const [value, setValue] = useState(settings.l1_min_price_rub);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setValue(settings.l1_min_price_rub);
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
      <Slider
        value={value}
        min={0}
        max={MIN_PRICE_MAX}
        step={null}
        disabled={locked || busy}
        onChange={(_, next) => {
          const raw = typeof next === "number" ? next : next[0];
          setValue(snapMinPrice(raw));
          setSaved(false);
        }}
        marks={[
          { value: 0, label: "0" },
          { value: 100_000, label: "100 тыс." },
          { value: 500_000, label: "500 тыс." },
          { value: MIN_PRICE_MAX, label: "5 млн" },
        ]}
        valueLabelDisplay="auto"
        valueLabelFormat={(v) => formatPrice(v)}
        sx={{ maxWidth: 520 }}
      />
      <Box>
        <Button variant="contained" size="small" disabled={locked || busy} onClick={() => void onSave()}>
          {copy.min_price_save}
        </Button>
      </Box>
      {error ? <Alert severity="error">{error}</Alert> : null}
      {saved ? <Alert severity="success">{copy.min_price_saved}</Alert> : null}
    </Stack>
  );
}

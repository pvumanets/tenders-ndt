import { useEffect, useState } from "react";
import { Alert, Button, Stack, TextField, Typography } from "@mui/material";
import { copy } from "../../copy";
import type { OperatorSettings } from "../../types";
import { putOperatorSettings } from "../../lib/inbox";
import { stripe } from "../../theme/palette";

function secretStatusLine(configured: boolean, hint: string): string {
  if (!configured) return copy.integrations_secret_missing;
  return copy.integrations_secret_configured.replace("{hint}", hint || "••••");
}

export default function SettingsProvodKey({
  settings,
  locked,
  onSaved,
}: {
  settings: OperatorSettings;
  locked: boolean;
  onSaved: (next: OperatorSettings) => void;
}) {
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  useEffect(() => {
    setValue("");
  }, [settings.provod_api_key.configured, settings.provod_api_key.hint]);

  async function onSave() {
    setError(null);
    setOk(null);
    const trimmed = value.trim();
    if (!trimmed) {
      setError(copy.integrations_secret_empty);
      return;
    }
    setBusy(true);
    try {
      const next = await putOperatorSettings({ provod_api_key: trimmed });
      onSaved(next);
      setValue("");
      setOk(copy.integrations_saved);
    } catch {
      setError(copy.integrations_save_failed);
    } finally {
      setBusy(false);
    }
  }

  async function onReset() {
    setError(null);
    setOk(null);
    setBusy(true);
    try {
      const next = await putOperatorSettings({ provod_api_key: null });
      onSaved(next);
      setValue("");
      setOk(copy.integrations_reset_done);
    } catch {
      setError(copy.integrations_save_failed);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Stack spacing={1.5}>
      <Typography variant="body2" sx={{ color: stripe.textMuted }}>
        {copy.integrations_provod_hint}
      </Typography>
      <Typography variant="caption" sx={{ color: stripe.textMuted }}>
        {secretStatusLine(settings.provod_api_key.configured, settings.provod_api_key.hint)}
      </Typography>
      <TextField
        type="password"
        label={copy.integrations_provod_label}
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          setOk(null);
        }}
        placeholder={copy.integrations_secret_placeholder}
        fullWidth
        size="small"
        disabled={locked || busy}
        autoComplete="off"
      />
      <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
        <Button variant="contained" size="small" disabled={locked || busy} onClick={() => void onSave()}>
          {copy.integrations_save}
        </Button>
        <Button variant="outlined" size="small" disabled={locked || busy} onClick={() => void onReset()}>
          {copy.integrations_reset_env}
        </Button>
      </Stack>
      {error ? <Alert severity="error">{error}</Alert> : null}
      {ok ? <Alert severity="success">{ok}</Alert> : null}
    </Stack>
  );
}

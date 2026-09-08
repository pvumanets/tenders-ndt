import { useEffect, useState } from "react";
import { Alert, Button, Stack, TextField, Typography } from "@mui/material";
import { copy } from "../../copy";
import type { OperatorSettings } from "../../types";
import { putOperatorSettings } from "../../lib/inbox";
import { stripe } from "../../theme/palette";

export default function SettingsAiPrompt({
  settings,
  locked,
  onSaved,
}: {
  settings: OperatorSettings;
  locked: boolean;
  onSaved: (next: OperatorSettings) => void;
}) {
  const [value, setValue] = useState(settings.ai_system_prompt);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  useEffect(() => {
    setValue(settings.ai_system_prompt);
  }, [settings.ai_system_prompt]);

  async function onSave() {
    setError(null);
    setOk(null);
    const trimmed = value.trim();
    if (!trimmed) {
      setError(copy.ai_prompt_invalid);
      return;
    }
    setBusy(true);
    try {
      const next = await putOperatorSettings({ ai_system_prompt: trimmed });
      onSaved(next);
      setOk(copy.ai_prompt_saved);
    } catch {
      setError(copy.ai_prompt_save_failed);
    } finally {
      setBusy(false);
    }
  }

  async function onReset() {
    setError(null);
    setOk(null);
    setBusy(true);
    try {
      const next = await putOperatorSettings({ ai_system_prompt: null });
      onSaved(next);
      setValue(next.ai_system_prompt);
      setOk(copy.ai_prompt_reset_done);
    } catch {
      setError(copy.ai_prompt_save_failed);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Stack spacing={1.5}>
      <Typography variant="body2" sx={{ color: stripe.textMuted }}>
        {copy.ai_prompt_hint}
      </Typography>
      <Typography variant="caption" sx={{ color: stripe.textMuted }}>
        {settings.ai_system_prompt_is_default
          ? copy.ai_prompt_default_badge
          : copy.ai_prompt_custom_badge}
      </Typography>
      <TextField
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          setOk(null);
        }}
        multiline
        minRows={10}
        fullWidth
        disabled={locked || busy}
        slotProps={{ htmlInput: { maxLength: 50_000 } }}
      />
      <Stack direction="row" spacing={1}>
        <Button variant="contained" size="small" disabled={locked || busy} onClick={() => void onSave()}>
          {copy.ai_prompt_save}
        </Button>
        <Button
          variant="outlined"
          size="small"
          disabled={locked || busy || settings.ai_system_prompt_is_default}
          onClick={() => void onReset()}
        >
          {copy.ai_prompt_reset}
        </Button>
      </Stack>
      {error ? <Alert severity="error">{error}</Alert> : null}
      {ok ? <Alert severity="success">{ok}</Alert> : null}
    </Stack>
  );
}

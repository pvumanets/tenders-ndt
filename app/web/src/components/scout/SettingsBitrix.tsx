import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  FormControlLabel,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { copy } from "../../copy";
import type { OperatorSettings } from "../../types";
import { putOperatorSettings } from "../../lib/inbox";
import { stripe } from "../../theme/palette";

function secretStatusLine(configured: boolean, hint: string): string {
  if (!configured) return copy.integrations_secret_missing;
  return copy.integrations_secret_configured.replace("{hint}", hint || "••••");
}

export default function SettingsBitrix({
  settings,
  locked,
  onSaved,
}: {
  settings: OperatorSettings;
  locked: boolean;
  onSaved: (next: OperatorSettings) => void;
}) {
  const [webhook, setWebhook] = useState("");
  const [assigned, setAssigned] = useState(settings.bitrix_assigned_by_id);
  const [source, setSource] = useState(settings.bitrix_lead_source_id);
  const [chat, setChat] = useState(settings.bitrix_chat_dialog_id);
  const [ops, setOps] = useState(settings.bitrix_ops_dialog_id);
  const [sendChat, setSendChat] = useState(settings.bitrix_send_chat);
  const [autoL1, setAutoL1] = useState(settings.bitrix_auto_l1_enabled);
  const [opsAlerts, setOpsAlerts] = useState(settings.bitrix_ops_alerts_enabled);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  useEffect(() => {
    setWebhook("");
    setAssigned(settings.bitrix_assigned_by_id);
    setSource(settings.bitrix_lead_source_id);
    setChat(settings.bitrix_chat_dialog_id);
    setOps(settings.bitrix_ops_dialog_id);
    setSendChat(settings.bitrix_send_chat);
    setAutoL1(settings.bitrix_auto_l1_enabled);
    setOpsAlerts(settings.bitrix_ops_alerts_enabled);
  }, [settings]);

  async function onSave() {
    setError(null);
    setOk(null);
    setBusy(true);
    try {
      const body: Parameters<typeof putOperatorSettings>[0] = {
        bitrix_assigned_by_id: assigned.trim() || null,
        bitrix_lead_source_id: source.trim() || null,
        bitrix_chat_dialog_id: chat.trim() || null,
        bitrix_ops_dialog_id: ops.trim() || null,
        bitrix_send_chat: sendChat,
        bitrix_auto_l1_enabled: autoL1,
        bitrix_ops_alerts_enabled: opsAlerts,
      };
      const trimmedWebhook = webhook.trim();
      if (trimmedWebhook) {
        body.bitrix_webhook_url = trimmedWebhook;
      }
      const next = await putOperatorSettings(body);
      onSaved(next);
      setWebhook("");
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
      const next = await putOperatorSettings({
        bitrix_webhook_url: null,
        bitrix_assigned_by_id: null,
        bitrix_lead_source_id: null,
        bitrix_chat_dialog_id: null,
        bitrix_ops_dialog_id: null,
        bitrix_send_chat: null,
        bitrix_auto_l1_enabled: null,
        bitrix_ops_alerts_enabled: null,
      });
      onSaved(next);
      setWebhook("");
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
        {copy.integrations_bitrix_hint}
      </Typography>
      <Typography variant="caption" sx={{ color: stripe.textMuted }}>
        {secretStatusLine(settings.bitrix_webhook_url.configured, settings.bitrix_webhook_url.hint)}
      </Typography>
      <TextField
        type="password"
        label={copy.integrations_bitrix_webhook_label}
        value={webhook}
        onChange={(e) => {
          setWebhook(e.target.value);
          setOk(null);
        }}
        placeholder={copy.integrations_secret_placeholder}
        fullWidth
        size="small"
        disabled={locked || busy}
        autoComplete="off"
      />
      <TextField
        label={copy.integrations_assigned_label}
        value={assigned}
        onChange={(e) => {
          setAssigned(e.target.value);
          setOk(null);
        }}
        fullWidth
        size="small"
        disabled={locked || busy}
      />
      <TextField
        label={copy.integrations_source_label}
        value={source}
        onChange={(e) => {
          setSource(e.target.value);
          setOk(null);
        }}
        fullWidth
        size="small"
        disabled={locked || busy}
      />
      <TextField
        label={copy.integrations_chat_label}
        value={chat}
        onChange={(e) => {
          setChat(e.target.value);
          setOk(null);
        }}
        fullWidth
        size="small"
        disabled={locked || busy}
      />
      <TextField
        label={copy.integrations_ops_label}
        value={ops}
        onChange={(e) => {
          setOps(e.target.value);
          setOk(null);
        }}
        fullWidth
        size="small"
        disabled={locked || busy}
      />
      <FormControlLabel
        control={
          <Switch
            checked={sendChat}
            disabled={locked || busy}
            onChange={(_, next) => {
              setSendChat(next);
              setOk(null);
            }}
          />
        }
        label={copy.integrations_send_chat}
      />
      <FormControlLabel
        control={
          <Switch
            checked={autoL1}
            disabled={locked || busy}
            onChange={(_, next) => {
              setAutoL1(next);
              setOk(null);
            }}
          />
        }
        label={copy.integrations_auto_l1}
      />
      <FormControlLabel
        control={
          <Switch
            checked={opsAlerts}
            disabled={locked || busy}
            onChange={(_, next) => {
              setOpsAlerts(next);
              setOk(null);
            }}
          />
        }
        label={copy.integrations_ops_alerts}
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

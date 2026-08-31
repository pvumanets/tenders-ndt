import { type FormEvent, useState } from "react";
import { Alert, Box, Button, Paper, TextField, Typography } from "@mui/material";
import { copy } from "../../copy";
import { login } from "../../lib/auth";
import { stripe } from "../../theme/palette";
import FieldRow from "../../vendor/personal/people/FieldRow";

export default function LoginScreen({ onSuccess }: { onSuccess: () => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(false);
    try {
      const ok = await login(username, password);
      if (ok) {
        onSuccess();
        return;
      }
      setError(true);
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        bgcolor: stripe.surfaceSubtle,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        px: 2,
      }}
    >
      <Paper
        elevation={0}
        sx={{
          width: 360,
          maxWidth: "100%",
          p: 3,
          border: `1px solid ${stripe.border}`,
          bgcolor: stripe.surface,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.25, mb: 2 }}>
          <Box
            component="img"
            src="/brand/logo.png"
            alt=""
            sx={{ width: 40, height: 40, flexShrink: 0 }}
          />
          <Typography variant="h2" sx={{ m: 0 }}>
            {copy.product_title}
          </Typography>
        </Box>
        <Box component="form" onSubmit={onSubmit}>
          <FieldRow label={copy.login_username}>
            <TextField
              fullWidth
              size="small"
              name="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              slotProps={{ htmlInput: { "aria-label": copy.login_username } }}
            />
          </FieldRow>
          <FieldRow label={copy.login_password}>
            <TextField
              fullWidth
              size="small"
              type="password"
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              slotProps={{ htmlInput: { "aria-label": copy.login_password } }}
            />
          </FieldRow>
          {error ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {copy.login_error}
            </Alert>
          ) : null}
          <Button type="submit" variant="contained" fullWidth disabled={busy}>
            {busy ? copy.login_busy : copy.login_submit}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}

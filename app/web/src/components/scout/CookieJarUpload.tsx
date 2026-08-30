import { useRef, useState } from "react";
import { Alert, Button, Stack, TextField, Typography } from "@mui/material";
import { copy } from "../../copy";
import { postPlatformCookies } from "../../lib/inbox";
import type { PlatformSession } from "../../types";
import { stripe } from "../../theme/palette";

export default function CookieJarUpload({
  platformId,
  locked,
  onUploaded,
}: {
  platformId: string;
  locked: boolean;
  onUploaded: (session: PlatformSession) => void;
}) {
  const [paste, setPaste] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  function parseJson(raw: string): unknown {
    const text = raw.trim();
    if (!text) throw new Error("invalid_cookies_json");
    const parsed = JSON.parse(text) as unknown;
    if (!Array.isArray(parsed) || parsed.length === 0) throw new Error("invalid_cookies_json");
    return parsed;
  }

  async function submit(raw: string) {
    setError(null);
    setOk(false);
    let payload: unknown;
    try {
      payload = parseJson(raw);
    } catch {
      setError(copy.cookies_invalid);
      return;
    }
    setBusy(true);
    try {
      const result = await postPlatformCookies(platformId, payload);
      onUploaded(result.session);
      setPaste("");
      if (fileRef.current) fileRef.current.value = "";
      setOk(true);
    } catch {
      setError(copy.cookies_invalid);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Stack spacing={1} sx={{ mt: 1 }}>
      <TextField
        multiline
        minRows={3}
        size="small"
        disabled={locked || busy}
        placeholder={copy.cookies_paste_placeholder}
        value={paste}
        onChange={(e) => {
          setPaste(e.target.value);
          setOk(false);
        }}
        slotProps={{ htmlInput: { "aria-label": copy.cookies_paste } }}
      />
      <Typography variant="caption" sx={{ color: stripe.textMuted }}>
        {copy.cookies_format_hint}
      </Typography>
      <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
        <Button
          size="small"
          variant="outlined"
          disabled={locked || busy}
          onClick={() => fileRef.current?.click()}
        >
          {copy.cookies_upload}
        </Button>
        <input
          ref={fileRef}
          type="file"
          accept="application/json,.json"
          hidden
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            const text = await file.text();
            void submit(text);
          }}
        />
        <Button
          size="small"
          variant="contained"
          disabled={locked || busy || !paste.trim()}
          onClick={() => void submit(paste)}
        >
          {busy ? copy.cookies_busy : copy.cookies_submit}
        </Button>
      </Stack>
      {error ? (
        <Alert severity="error" sx={{ py: 0 }}>
          {error}
        </Alert>
      ) : null}
      {ok ? (
        <Alert severity="success" sx={{ py: 0 }}>
          {copy.cookies_ok}
        </Alert>
      ) : null}
    </Stack>
  );
}

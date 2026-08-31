import { useRef, useState } from "react";
import { Alert, Button, Collapse, Stack, TextField, Typography } from "@mui/material";
import { copy } from "../../copy";
import { postPlatformCookies } from "../../lib/inbox";
import type { PlatformSession } from "../../types";
import { stripe } from "../../theme/palette";

function sessionCaption(session: PlatformSession | undefined): string | null {
  if (session === "missing") return copy.cookies_missing;
  if (session === "expired") return copy.cookies_expired;
  if (session === "ok") return copy.cookies_on_server;
  return null;
}

export default function CookieJarUpload({
  platformId,
  locked,
  session,
  onUploaded,
}: {
  platformId: string;
  locked: boolean;
  session?: PlatformSession;
  onUploaded: (session: PlatformSession) => void;
}) {
  const [paste, setPaste] = useState("");
  const [pasteOpen, setPasteOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const caption = sessionCaption(session);

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
      setPasteOpen(false);
      if (fileRef.current) fileRef.current.value = "";
      setOk(true);
    } catch {
      setError(copy.cookies_invalid);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Stack spacing={0.75} sx={{ mt: 0.75 }}>
      {caption ? (
        <Typography variant="caption" sx={{ color: stripe.textMuted }}>
          {caption}
        </Typography>
      ) : null}
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
          variant="text"
          disabled={locked || busy}
          onClick={() => setPasteOpen((open) => !open)}
        >
          {pasteOpen ? copy.cookies_paste_hide : copy.cookies_paste}
        </Button>
      </Stack>
      <Collapse in={pasteOpen} unmountOnExit>
        <Stack spacing={0.75} sx={{ pt: 0.5 }}>
          <TextField
            multiline
            minRows={2}
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
          <Button
            size="small"
            variant="contained"
            disabled={locked || busy || !paste.trim()}
            onClick={() => void submit(paste)}
            sx={{ alignSelf: "flex-start" }}
          >
            {busy ? copy.cookies_busy : copy.cookies_submit}
          </Button>
        </Stack>
      </Collapse>
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

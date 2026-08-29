import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Collapse,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { copy } from "../../copy";
import { stripe } from "../../theme/palette";
import type { TechStatus } from "../../types";

export default function TechDiagnostics({
  status,
  forceOpen = false,
}: {
  status: TechStatus;
  forceOpen?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (forceOpen) setOpen(true);
  }, [forceOpen]);

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", mb: 1 }}>
        <Typography variant="subtitle2" sx={{ flex: 1 }}>
          {copy.run_section_diagnostics}
        </Typography>
        <Button size="small" onClick={() => setOpen((v) => !v)}>
          {open ? copy.diagnostics_collapse : copy.diagnostics_expand}
        </Button>
      </Stack>
      <Collapse in={open} unmountOnExit>
        <Stack spacing={1.5}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              {copy.run_path_label}
            </Typography>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ mt: 0.5 }}>
              <TextField
                size="small"
                fullWidth
                value={status.run_dir}
                slotProps={{ input: { readOnly: true } }}
              />
              <Button
                size="small"
                variant="outlined"
                sx={{ alignSelf: { xs: "flex-start", sm: "center" }, flexShrink: 0 }}
                disabled={!status.run_dir}
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(status.run_dir);
                    setCopied(true);
                    window.setTimeout(() => setCopied(false), 1500);
                  } catch {
                    /* ignore */
                  }
                }}
              >
                {copied ? copy.run_path_copied : copy.run_path_copy}
              </Button>
            </Stack>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              {copy.log_title}
            </Typography>
            <Box
              component="ul"
              sx={{
                m: 0,
                mt: 0.5,
                p: 1.5,
                listStyle: "none",
                bgcolor: stripe.surfaceSubtle,
                border: `1px solid ${stripe.border}`,
                borderRadius: 1,
                fontFamily: "ui-monospace, Consolas, monospace",
                fontSize: 12,
                maxHeight: 220,
                overflow: "auto",
              }}
            >
              {status.log.length === 0 ? (
                <li>{copy.log_empty}</li>
              ) : (
                status.log.map((line, i) => (
                  <li
                    key={`${line.t}-${i}`}
                    style={{ color: line.level === "error" ? stripe.critical : undefined }}
                  >
                    {line.t} {line.msg}
                  </li>
                ))
              )}
            </Box>
          </Box>
        </Stack>
      </Collapse>
    </Box>
  );
}

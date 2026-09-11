import { Alert, Button, Stack } from "@mui/material";
import { copy } from "../../copy";
import type { PlatformRow } from "../../types";
import { needsSessionBanner } from "../../lib/slot-status";

export default function SessionExpiryBanner({
  platforms,
  onOpenSettings,
  onOpenHelp,
}: {
  platforms: PlatformRow[];
  onOpenSettings: () => void;
  onOpenHelp: () => void;
}) {
  if (!needsSessionBanner(platforms)) return null;
  return (
    <Alert
      severity="warning"
      sx={{ mb: 1.5 }}
      action={
        <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
          <Button color="inherit" size="small" onClick={onOpenHelp}>
            {copy.auto_session_banner_help}
          </Button>
          <Button color="inherit" size="small" onClick={onOpenSettings}>
            {copy.auto_session_banner_action}
          </Button>
        </Stack>
      }
    >
      {copy.auto_session_banner}
    </Alert>
  );
}

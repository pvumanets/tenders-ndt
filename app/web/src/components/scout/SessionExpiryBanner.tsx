import { Alert, Button } from "@mui/material";
import { copy } from "../../copy";
import type { PlatformRow } from "../../types";
import { needsSessionBanner } from "../../lib/slot-status";

export default function SessionExpiryBanner({
  platforms,
  onOpenSettings,
}: {
  platforms: PlatformRow[];
  onOpenSettings: () => void;
}) {
  if (!needsSessionBanner(platforms)) return null;
  return (
    <Alert
      severity="warning"
      sx={{ mb: 1.5 }}
      action={
        <Button color="inherit" size="small" onClick={onOpenSettings}>
          {copy.auto_session_banner_action}
        </Button>
      }
    >
      {copy.auto_session_banner}
    </Alert>
  );
}

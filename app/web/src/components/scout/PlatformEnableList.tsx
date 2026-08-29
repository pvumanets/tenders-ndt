import { Alert, Box, FormControlLabel, Stack, Switch, Typography } from "@mui/material";
import { copy } from "../../copy";
import { formatPlatformSessionLine } from "../../lib/inbox";
import { stripe } from "../../theme/palette";
import type { PlatformRow } from "../../types";

export default function PlatformEnableList({
  platforms,
  locked,
  onToggle,
}: {
  platforms: PlatformRow[];
  locked: boolean;
  onToggle: (platform: PlatformRow, enabled: boolean) => void;
}) {
  if (platforms.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        {copy.platforms_none_enabled}
      </Typography>
    );
  }

  return (
    <Stack spacing={1}>
      {platforms.map((platform) => {
        const needsHint =
          platform.enabled &&
          (platform.session === "missing" || platform.session === "expired");
        return (
          <Box
            key={platform.platform_id}
            sx={{
              py: 0.75,
              px: 0.5,
              borderBottom: `1px solid ${stripe.border}`,
            }}
          >
            <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
              <Typography sx={{ flex: 1, minWidth: 0 }} noWrap>
                {platform.name}
              </Typography>
              <FormControlLabel
                sx={{ mr: 0, flexShrink: 0 }}
                control={
                  <Switch
                    size="small"
                    checked={platform.enabled}
                    disabled={locked}
                    onChange={(_, checked) => onToggle(platform, checked)}
                    slotProps={{
                      input: {
                        "aria-label": `${copy.platform_participate}: ${platform.name}`,
                      },
                    }}
                  />
                }
                label={copy.platform_participate}
              />
            </Stack>
            <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
              {formatPlatformSessionLine(platform)}
            </Typography>
            {needsHint ? (
              <Alert severity="warning" sx={{ mt: 0.75, py: 0 }}>
                {copy.session_hint_docs}
              </Alert>
            ) : null}
          </Box>
        );
      })}
    </Stack>
  );
}

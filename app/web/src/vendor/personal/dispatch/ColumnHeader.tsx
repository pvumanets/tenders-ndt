import { Box, Typography } from "@mui/material";
import {
  columnHeaderIdentitySx,
  columnHeaderStripSx,
  columnHeaderTitleSx,
} from "../layout/column-header-typography";

export type ColumnHeaderVariant =
  | "dispatchSite"
  | "planningSite"
  | "reserve"
  | "inTransit"
  | "specialTask";

export interface ColumnHeaderProps {
  title?: string;
  city?: string;
  siteName?: string;
  plantName?: string;
  variant?: ColumnHeaderVariant;
  onSiteCount?: number;
  peopleCount?: number;
  /** Simple count line when metrics strip not used */
  countLabel?: string;
}

/** Vendored from personal ColumnHeader — metrics/domain strip simplified to countLabel. */
export default function ColumnHeader({
  title,
  city: cityProp,
  siteName,
  plantName,
  variant = "specialTask",
  onSiteCount,
  peopleCount,
  countLabel,
}: ColumnHeaderProps) {
  const city = cityProp ?? title ?? "";
  const showIdentityUnderCity =
    variant !== "dispatchSite" && variant !== "planningSite";
  const identityLine =
    siteName && variant !== "reserve" && variant !== "specialTask"
      ? `${siteName}${plantName ? ` · ${plantName}` : ""}`
      : plantName;

  const strip =
    countLabel ??
    (peopleCount !== undefined
      ? String(peopleCount)
      : onSiteCount !== undefined
        ? String(onSiteCount)
        : null);

  return (
    <Box sx={{ mb: 1, px: 0.25 }}>
      <Box sx={{ minWidth: 0 }}>
        <Typography component="h6" sx={columnHeaderTitleSx}>
          {city}
        </Typography>
        {showIdentityUnderCity && identityLine && variant !== "specialTask" && (
          <Typography component="span" variant="caption" sx={columnHeaderIdentitySx}>
            {identityLine}
          </Typography>
        )}
        {variant === "specialTask" && plantName && (
          <Typography component="span" variant="caption" sx={columnHeaderIdentitySx}>
            {plantName}
          </Typography>
        )}
      </Box>
      {strip != null && (
        <Box
          sx={{
            mt: 1,
            pt: 1,
            pb: 1,
            borderTop: 1,
            borderColor: "divider",
            width: "100%",
          }}
        >
          <Typography variant="caption" color="text.secondary" sx={columnHeaderStripSx}>
            {strip}
          </Typography>
        </Box>
      )}
    </Box>
  );
}

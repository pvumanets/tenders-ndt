import { useState } from "react";
import { Box, Tooltip, Typography } from "@mui/material";
import { copy } from "../../copy";
import { getPlatform } from "../../platforms";
import { stripe } from "../../theme/palette";

const DISPLAY = 18;

/** Favicon/logo of source ЭТП — 16–20px; tooltip = label. */
export default function PlatformIcon({
  platformId,
  size = DISPLAY,
}: {
  platformId: string;
  size?: number;
}) {
  const meta = getPlatform(platformId);
  const [broken, setBroken] = useState(false);
  const aria = copy.platform_icon_aria.replace("{name}", meta.label_ru);

  const fallback = (
    <Box
      aria-hidden
      sx={{
        width: size,
        height: size,
        borderRadius: "3px",
        bgcolor: stripe.borderHover,
        display: "grid",
        placeItems: "center",
        flexShrink: 0,
      }}
    >
      <Typography
        component="span"
        sx={{
          fontSize: size <= 16 ? 7 : 8,
          fontWeight: 600,
          color: stripe.navy,
          lineHeight: 1,
          letterSpacing: 0,
        }}
      >
        {meta.initials.slice(0, 2)}
      </Typography>
    </Box>
  );

  return (
    <Tooltip title={meta.label_ru} describeChild>
      <Box
        component="span"
        role="img"
        aria-label={aria}
        title={meta.label_ru}
        sx={{
          display: "inline-flex",
          width: size,
          height: size,
          flexShrink: 0,
          lineHeight: 0,
        }}
      >
        {broken ? (
          fallback
        ) : (
          <Box
            component="img"
            src={meta.logo}
            alt=""
            width={size}
            height={size}
            onError={() => setBroken(true)}
            sx={{
              width: size,
              height: size,
              objectFit: "contain",
              borderRadius: "3px",
              display: "block",
            }}
          />
        )}
      </Box>
    </Tooltip>
  );
}

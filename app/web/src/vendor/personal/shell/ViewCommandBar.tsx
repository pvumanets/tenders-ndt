import { forwardRef } from "react";
import { Box, Divider, type SxProps, type Theme } from "@mui/material";
import type { SystemStyleObject } from "@mui/system";
import { viewCommandBarLayout } from "../layout/view-command-bar";
import { stripe } from "../../../theme/palette";

interface ViewCommandBarProps {
  children: React.ReactNode;
  sticky?: boolean;
  sx?: SxProps<Theme>;
}

interface ViewCommandBarSlotProps {
  children: React.ReactNode;
  sx?: SxProps<Theme>;
}

function mergeSx(...parts: (SxProps<Theme> | false | undefined)[]): SxProps<Theme> {
  return parts.filter(Boolean) as SxProps<Theme>;
}

function buildSlotSx(slot: "start" | "center" | "end" | "utility"): SystemStyleObject<Theme> {
  switch (slot) {
    case "start":
      return {
        display: "flex",
        alignItems: "center",
        gap: viewCommandBarLayout.groupGap,
        minWidth: 0,
        justifySelf: "start",
      };
    case "center":
      return {
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: viewCommandBarLayout.groupGap,
        minWidth: 0,
        justifySelf: "center",
      };
    case "end":
      return {
        display: "flex",
        alignItems: "center",
        justifyContent: "flex-end",
        gap: viewCommandBarLayout.groupGap,
        minWidth: 0,
        justifySelf: "end",
      };
    default:
      return {
        display: "flex",
        alignItems: "center",
        gap: viewCommandBarLayout.groupGap,
        flexShrink: 0,
        minWidth: 0,
      };
  }
}

const ViewCommandBarStart = forwardRef<HTMLDivElement, ViewCommandBarSlotProps>(
  function ViewCommandBarStart({ children, sx }, ref) {
    return (
      <Box ref={ref} sx={mergeSx(buildSlotSx("start"), sx)}>
        {children}
      </Box>
    );
  },
);

const ViewCommandBarCenter = forwardRef<HTMLDivElement, ViewCommandBarSlotProps>(
  function ViewCommandBarCenter({ children, sx }, ref) {
    return (
      <Box ref={ref} sx={mergeSx(buildSlotSx("center"), sx)}>
        {children}
      </Box>
    );
  },
);

const ViewCommandBarEnd = forwardRef<HTMLDivElement, ViewCommandBarSlotProps>(
  function ViewCommandBarEnd({ children, sx }, ref) {
    return (
      <Box ref={ref} sx={mergeSx(buildSlotSx("end"), sx)}>
        {children}
      </Box>
    );
  },
);

const ViewCommandBarUtility = forwardRef<HTMLDivElement, ViewCommandBarSlotProps>(
  function ViewCommandBarUtility({ children, sx }, ref) {
    return (
      <Box ref={ref} sx={mergeSx(buildSlotSx("utility"), sx)}>
        {children}
      </Box>
    );
  },
);

const ViewCommandBarGroup = forwardRef<HTMLDivElement, ViewCommandBarSlotProps>(
  function ViewCommandBarGroup({ children, sx }, ref) {
    return (
      <Box
        ref={ref}
        sx={mergeSx(
          {
            display: "flex",
            alignItems: "center",
            gap: viewCommandBarLayout.groupGap,
            minWidth: 0,
            flexWrap: "nowrap",
          },
          sx,
        )}
      >
        {children}
      </Box>
    );
  },
);

function ViewCommandBarSeparator() {
  return (
    <Divider
      orientation="vertical"
      flexItem
      sx={{
        height: viewCommandBarLayout.separatorHeight,
        alignSelf: "center",
        borderColor: stripe.border,
      }}
    />
  );
}

const ViewCommandBarRoot = forwardRef<HTMLDivElement, ViewCommandBarProps>(
  function ViewCommandBarRoot({ children, sticky = false, sx }, ref) {
    return (
      <Box
        ref={ref}
        sx={mergeSx(
          {
            display: "grid",
            gridTemplateColumns: "1fr auto 1fr",
            alignItems: "center",
            columnGap: viewCommandBarLayout.outerGap,
            rowGap: viewCommandBarLayout.outerGap,
            minHeight: viewCommandBarLayout.barMinHeight,
            py: viewCommandBarLayout.paddingY,
            px: viewCommandBarLayout.paddingX,
            mb: viewCommandBarLayout.marginBottom,
            boxSizing: "border-box",
            border: `1px solid ${stripe.border}`,
            borderRadius: `${viewCommandBarLayout.borderRadius}px`,
            backgroundColor: stripe.surface,
          },
          sticky && {
            position: "sticky",
            top: 0,
            zIndex: 1,
          },
          sx,
        )}
      >
        {children}
      </Box>
    );
  },
);

type ViewCommandBarComponent = typeof ViewCommandBarRoot & {
  Start: typeof ViewCommandBarStart;
  Center: typeof ViewCommandBarCenter;
  End: typeof ViewCommandBarEnd;
  Utility: typeof ViewCommandBarUtility;
  Group: typeof ViewCommandBarGroup;
  Separator: typeof ViewCommandBarSeparator;
};

const ViewCommandBar = Object.assign(ViewCommandBarRoot, {
  Start: ViewCommandBarStart,
  Center: ViewCommandBarCenter,
  End: ViewCommandBarEnd,
  Utility: ViewCommandBarUtility,
  Group: ViewCommandBarGroup,
  Separator: ViewCommandBarSeparator,
}) as ViewCommandBarComponent;

export default ViewCommandBar;

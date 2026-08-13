import { Children, type ReactNode } from "react";
import { Paper, Stack, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { semantic, stripe } from "../../../theme/palette";
import { stripeScrollbarSx } from "../../../theme/scrollbars";
import ColumnHeader, { type ColumnHeaderVariant } from "./ColumnHeader";

export interface BoardColumnProps {
  title?: string;
  city?: string;
  siteName?: string;
  plantName?: string;
  headerVariant?: ColumnHeaderVariant;
  peopleCount?: number;
  countLabel?: string;
  emptyMessage?: string;
  columnVariant?: "fixed" | "scroll";
  /** Scout board: share row width; keep personal minWidth, drop maxWidth cap. */
  fluid?: boolean;
  children?: ReactNode;
}

/** Vendored from personal BoardColumn — DnD/domain removed; children slot for LotMiniCard. */
export default function BoardColumn({
  title,
  city: cityProp,
  siteName,
  plantName,
  headerVariant = "specialTask",
  peopleCount,
  countLabel,
  emptyMessage = "Нет лотов",
  columnVariant = "scroll",
  fluid = false,
  children,
}: BoardColumnProps) {
  const theme = useTheme();
  const city = cityProp ?? title ?? "";
  const childList = Children.toArray(children);

  return (
    <Paper
      elevation={0}
      sx={{
        p: 1.25,
        minWidth: { xs: 0, md: theme.density.column.minWidth },
        ...(fluid
          ? {
              flex: { xs: "none", md: "1 1 0" },
              maxWidth: "none",
              width: { xs: "100%", md: 0 },
              height: { xs: "auto", md: "100%" },
            }
          : {
              maxWidth:
                columnVariant === "fixed"
                  ? theme.density.column.maxWidthFixed
                  : theme.density.column.maxWidthScroll,
              flexShrink: 0,
            }),
        boxSizing: "border-box",
        bgcolor: columnVariant === "fixed" ? semantic.surfaceFixed : semantic.surfaceScroll,
        border: `1px solid ${stripe.border}`,
        borderRadius: `${theme.density.radius.sm}px`,
        display: "flex",
        flexDirection: "column",
        height: fluid ? { xs: "auto", md: "100%" } : "100%",
        minHeight: 0,
        boxShadow: "none",
        overflow: "hidden",
        "&:hover": { boxShadow: "none" },
      }}
    >
      <ColumnHeader
        city={city}
        siteName={siteName}
        plantName={plantName}
        variant={headerVariant}
        peopleCount={peopleCount}
        countLabel={countLabel ?? (peopleCount !== undefined ? `${peopleCount}` : undefined)}
      />
      <Stack
        spacing={0.75}
        sx={{
          overflowY: { xs: "visible", md: "auto" },
          overflowX: "hidden",
          flex: { xs: "none", md: 1 },
          minWidth: 0,
          ...stripeScrollbarSx,
        }}
      >
        {childList.length === 0 ? (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              py: 2,
              px: 1,
              textAlign: "center",
              border: `1px dashed ${stripe.border}`,
              borderRadius: `${theme.density.radius.sm}px`,
            }}
          >
            {emptyMessage}
          </Typography>
        ) : (
          childList
        )}
      </Stack>
    </Paper>
  );
}

import { Children, useState, type DragEvent, type ReactNode } from "react";
import { Paper, Stack, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import type { TeachBucket } from "../../../types";
import { createBoardDropHandlers } from "../../../lib/board-dnd";
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
  /** HTML5 drop zone (ndt-personal pattern). */
  dropBucket?: TeachBucket;
  onDropLot?: (tenderId: string, bucket: TeachBucket) => void;
}

/** Vendored from personal BoardColumn — HTML5 DnD restored for Scout teach (092). */
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
  dropBucket,
  onDropLot,
}: BoardColumnProps) {
  const theme = useTheme();
  const city = cityProp ?? title ?? "";
  const childList = Children.toArray(children);
  const [dropActive, setDropActive] = useState(false);

  const dropHandlers =
    dropBucket && onDropLot ? createBoardDropHandlers(dropBucket, onDropLot) : null;

  function handleDropZoneOver(event: DragEvent) {
    setDropActive(true);
    dropHandlers?.onDragOver(event);
  }

  function handleDropZoneLeave() {
    setDropActive(false);
  }

  function handleDropZoneDrop(event: DragEvent) {
    setDropActive(false);
    dropHandlers?.onDrop(event);
  }

  return (
    <Paper
      elevation={0}
      onDragOver={dropHandlers ? handleDropZoneOver : undefined}
      onDragLeave={dropHandlers ? handleDropZoneLeave : undefined}
      onDrop={dropHandlers ? handleDropZoneDrop : undefined}
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
        border: dropActive ? `2px solid ${stripe.blurple}` : `1px solid ${stripe.border}`,
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

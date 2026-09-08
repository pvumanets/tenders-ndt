import { Box } from "@mui/material";
import { useDroppable } from "@dnd-kit/core";
import type { ReactNode } from "react";
import type { TeachBucket } from "../../types";
import { stripe } from "../../theme/palette";

export default function DroppableColumn({
  id,
  children,
}: {
  id: TeachBucket;
  children: ReactNode;
}) {
  const { setNodeRef, isOver } = useDroppable({ id });
  return (
    <Box
      ref={setNodeRef}
      sx={{
        flex: { xs: "none", md: "1 1 0" },
        minWidth: 0,
        display: "flex",
        flexDirection: "column",
        outline: isOver ? `2px solid ${stripe.blurple}` : "none",
        outlineOffset: 2,
        borderRadius: 1,
        height: { xs: "auto", md: "100%" },
        minHeight: { xs: 200, md: 0 },
        "& > *": { flex: 1, minHeight: 0, width: "100%" },
      }}
    >
      {children}
    </Box>
  );
}

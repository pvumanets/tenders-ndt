import { Box } from "@mui/material";
import { useDroppable } from "@dnd-kit/core";
import type { ReactNode } from "react";
import type { TeachBucket } from "../../types";
import { stripe } from "../../theme/palette";

/** Thin droppable shell — must not collapse BoardColumn height (overflow:hidden). */
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
        width: { xs: "100%", md: 0 },
        display: "flex",
        flexDirection: "column",
        alignSelf: "stretch",
        outline: isOver ? `2px solid ${stripe.blurple}` : "none",
        outlineOffset: 2,
        borderRadius: 1,
      }}
    >
      {children}
    </Box>
  );
}

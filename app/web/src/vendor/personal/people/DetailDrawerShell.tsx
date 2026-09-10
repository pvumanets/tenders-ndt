import { Box, Drawer } from "@mui/material";
import type { ReactNode } from "react";

export interface DetailDrawerShellProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  /** Paper width on sm+ (default 400). */
  width?: number;
}

export default function DetailDrawerShell({
  open,
  onClose,
  children,
  width = 400,
}: DetailDrawerShellProps) {
  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        "& .MuiDrawer-paper": {
          width: { xs: "100%", sm: width },
          maxWidth: "100%",
          p: 0,
        },
      }}
    >
      <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>{children}</Box>
    </Drawer>
  );
}

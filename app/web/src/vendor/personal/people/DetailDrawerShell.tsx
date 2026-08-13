import { Box, Drawer } from "@mui/material";
import type { ReactNode } from "react";

export interface DetailDrawerShellProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}

/** Vendored from personal PersonDetailDrawerShell (400px). */
export default function DetailDrawerShell({ open, onClose, children }: DetailDrawerShellProps) {
  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        "& .MuiDrawer-paper": {
          width: { xs: "100%", sm: 400 },
          maxWidth: "100%",
          p: 0,
        },
      }}
    >
      <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>{children}</Box>
    </Drawer>
  );
}

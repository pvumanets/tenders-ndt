import { CssBaseline, ThemeProvider } from "@mui/material";
import type { ReactNode } from "react";
import { createAppTheme } from "../theme/theme";

const theme = createAppTheme('"Inter", "Roboto", "Helvetica", "Arial", sans-serif');

export default function ThemeRegistry({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
}

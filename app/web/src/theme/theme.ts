import { createTheme } from "@mui/material/styles";
import { buildComponents } from "./components";
import { density } from "./density";
import { semantic, stripe } from "./palette";
import { muiShadows } from "./shadows";
import { buildTypography } from "./typography";

declare module "@mui/material/styles" {
  interface Theme {
    customTokens: typeof semantic;
    stripe: typeof stripe;
    density: typeof density;
  }
  interface ThemeOptions {
    customTokens?: typeof semantic;
    stripe?: typeof stripe;
    density?: typeof density;
  }
}

export function createAppTheme(fontFamily: string) {
  return createTheme({
    palette: {
      mode: "light",
      primary: {
        main: stripe.blurple,
        dark: stripe.blurpleHover,
        light: "#8B85FF",
        contrastText: "#FFFFFF",
      },
      secondary: {
        main: stripe.navy,
        contrastText: "#FFFFFF",
      },
      background: {
        default: stripe.surfaceSubtle,
        paper: stripe.surface,
      },
      text: {
        primary: stripe.text,
        secondary: stripe.textMuted,
      },
      divider: stripe.border,
      success: {
        main: stripe.success,
      },
      warning: {
        main: stripe.warning,
      },
      error: {
        main: stripe.critical,
      },
      info: {
        main: stripe.info,
      },
    },
    typography: buildTypography(fontFamily),
    shape: {
      borderRadius: density.radius.md,
    },
    shadows: muiShadows,
    customTokens: semantic,
    stripe,
    density,
    components: buildComponents(),
  });
}

/** Default theme — overridden by ThemeRegistry with Inter */
const theme = createAppTheme('"Inter", "Roboto", "Helvetica", "Arial", sans-serif');
export default theme;

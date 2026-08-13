import type { SxProps, Theme } from "@mui/material/styles";
import { stripe } from "./palette";

/** Stripe-style thin scrollbars — reusable sx fragment */
export const stripeScrollbarSx: SxProps<Theme> = {
  scrollbarWidth: "thin",
  scrollbarColor: `${stripe.borderHover} transparent`,
  "&::-webkit-scrollbar": {
    width: 6,
    height: 6,
  },
  "&::-webkit-scrollbar-track": {
    backgroundColor: "transparent",
  },
  "&::-webkit-scrollbar-thumb": {
    backgroundColor: stripe.borderHover,
    borderRadius: 9999,
    border: "2px solid transparent",
    backgroundClip: "padding-box",
  },
  "&::-webkit-scrollbar-thumb:hover": {
    backgroundColor: stripe.textMuted,
  },
  "&::-webkit-scrollbar-corner": {
    backgroundColor: "transparent",
  },
};

/** Global CSS for scrollbars on root scroll containers */
export const stripeScrollbarGlobalCss = {
  "*": {
    scrollbarWidth: "thin",
    scrollbarColor: `${stripe.borderHover} transparent`,
  },
  "*::-webkit-scrollbar": {
    width: 6,
    height: 6,
  },
  "*::-webkit-scrollbar-track": {
    backgroundColor: "transparent",
  },
  "*::-webkit-scrollbar-thumb": {
    backgroundColor: stripe.borderHover,
    borderRadius: 9999,
    border: "2px solid transparent",
    backgroundClip: "padding-box",
  },
  "*::-webkit-scrollbar-thumb:hover": {
    backgroundColor: stripe.textMuted,
  },
  "*::-webkit-scrollbar-corner": {
    backgroundColor: "transparent",
  },
} as const;

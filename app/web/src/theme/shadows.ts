import type { Shadows } from "@mui/material/styles";

/** Stripe-style shadows — flat by default, subtle on hover */
export const stripeShadows = {
  none: "none",
  sm: "0 1px 1px rgba(0, 0, 0, 0.03), 0 3px 6px rgba(18, 42, 66, 0.08)",
  md: "0 2px 4px rgba(0, 0, 0, 0.04), 0 6px 16px rgba(18, 42, 66, 0.1)",
  dialog: "0 8px 32px rgba(18, 42, 66, 0.12), 0 2px 8px rgba(0, 0, 0, 0.06)",
  focusRing: `0 0 0 3px rgba(99, 91, 255, 0.25)`,
} as const;

/** MUI expects 25 shadow entries — use flat shadows throughout */
export const muiShadows: Shadows = [
  "none",
  stripeShadows.sm,
  stripeShadows.sm,
  stripeShadows.md,
  stripeShadows.md,
  stripeShadows.md,
  stripeShadows.md,
  stripeShadows.md,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
  stripeShadows.dialog,
];

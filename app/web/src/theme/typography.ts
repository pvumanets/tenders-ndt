import type { TypographyVariantsOptions } from "@mui/material/styles";
import { density } from "./density";
import { stripe } from "./palette";

const { font, weight } = density;

export function buildTypography(fontFamily: string): TypographyVariantsOptions {
  return {
    fontFamily,
    fontSize: font.md,
    h1: {
      fontSize: `${font.xxl}px`,
      fontWeight: weight.medium,
      lineHeight: 1.3,
      color: stripe.navy,
      letterSpacing: "-0.02em",
    },
    h2: {
      fontSize: `${font.xl}px`,
      fontWeight: weight.medium,
      lineHeight: 1.35,
      color: stripe.navy,
      letterSpacing: "-0.02em",
    },
    h3: {
      fontSize: `${font.lg}px`,
      fontWeight: weight.medium,
      lineHeight: 1.4,
      color: stripe.navy,
      letterSpacing: "-0.01em",
    },
    h4: {
      fontSize: `${font.lg}px`,
      fontWeight: weight.medium,
      lineHeight: 1.4,
      color: stripe.navy,
    },
    h5: {
      fontSize: `${font.md}px`,
      fontWeight: weight.medium,
      lineHeight: 1.5,
      color: stripe.navy,
    },
    h6: {
      fontSize: `${font.md}px`,
      fontWeight: weight.medium,
      lineHeight: 1.5,
      color: stripe.navy,
    },
    subtitle1: {
      fontSize: `${font.md}px`,
      fontWeight: weight.medium,
      lineHeight: 1.5,
      color: stripe.text,
    },
    subtitle2: {
      fontSize: `${font.sm}px`,
      fontWeight: weight.medium,
      lineHeight: 1.5,
      color: stripe.text,
    },
    body1: {
      fontSize: `${font.md}px`,
      fontWeight: weight.regular,
      lineHeight: 1.5715,
      color: stripe.text,
    },
    body2: {
      fontSize: `${font.sm}px`,
      fontWeight: weight.regular,
      lineHeight: 1.538,
      color: stripe.text,
    },
    caption: {
      fontSize: `${font.xs}px`,
      fontWeight: weight.regular,
      lineHeight: 1.5,
      color: stripe.textMuted,
    },
    button: {
      fontSize: `${font.md}px`,
      fontWeight: weight.regular,
      lineHeight: 1.5,
      textTransform: "none" as const,
    },
    overline: {
      fontSize: `${font.xs}px`,
      fontWeight: weight.medium,
      lineHeight: 1.5,
      letterSpacing: "0.06em",
      textTransform: "uppercase" as const,
      color: stripe.textMuted,
    },
  };
}

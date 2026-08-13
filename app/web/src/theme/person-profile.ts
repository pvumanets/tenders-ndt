import type { SxProps, Theme } from "@mui/material/styles";
import { density } from "./density";
import { stripe } from "./palette";

const { font, weight } = density;

/** Typography tokens for person profile cards — ADR-018 */
export const personProfileTokens = {
  profileName: {
    fontSize: "25px",
    fontWeight: 100,
    lineHeight: 1.25,
    color: stripe.navy,
    margin: 0,
  },
  sectionTitle: {
    fontSize: `${font.lg}px`,
    fontWeight: 600,
    lineHeight: 1.4,
    color: stripe.text,
  },
  fieldLabel: {
    fontSize: `${font.sm}px`,
    fontWeight: weight.regular,
    lineHeight: 1.5,
    color: stripe.textMuted,
  },
  fieldValue: {
    fontSize: `${font.md}px`,
    fontWeight: weight.medium,
    lineHeight: 1.5,
    color: stripe.text,
  },
  fieldValueEmpty: {
    fontSize: `${font.md}px`,
    fontWeight: weight.regular,
    lineHeight: 1.5,
    color: stripe.textMuted,
    fontStyle: "italic",
  },
} as const satisfies Record<string, SxProps<Theme>>;

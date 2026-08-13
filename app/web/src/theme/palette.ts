/** Stripe Dashboard design tokens */
export const stripe = {
  blurple: "#635BFF",
  blurpleHover: "#5851E5",
  blurpleSoft: "rgba(99, 91, 255, 0.08)",
  blurpleFocus: "rgba(99, 91, 255, 0.25)",
  navy: "#0A2540",
  text: "#3C4257",
  textMuted: "#697386",
  border: "#E3E8EE",
  borderHover: "#C1C9D2",
  surface: "#FFFFFF",
  surfaceSubtle: "#F6F9FC",
  success: "#09825D",
  successSoft: "rgba(9, 130, 93, 0.1)",
  warning: "#EFA32F",
  warningSoft: "rgba(239, 163, 47, 0.1)",
  critical: "#C62828",
  criticalSoft: "rgba(198, 40, 40, 0.08)",
  info: "#0073E6",
  infoSoft: "rgba(0, 115, 230, 0.08)",
} as const;

/** Dispatch semantic aliases — map to Stripe palette only */
export const semantic = {
  warning30d: stripe.warning,
  warning30dSoft: stripe.warningSoft,
  critical50d: stripe.critical,
  critical50dSoft: stripe.criticalSoft,
  planDraft: stripe.blurple,
  planDraftSoft: stripe.blurpleSoft,
  permitInfo: stripe.textMuted,
  permitInfoSoft: stripe.surfaceSubtle,
  medInfo: stripe.info,
  medInfoSoft: stripe.infoSoft,
  onboarding: stripe.blurple,
  onboardingSoft: stripe.blurpleSoft,
  peripheral: stripe.textMuted,
  peripheralSoft: stripe.surfaceSubtle,
  surfaceFixed: stripe.surfaceSubtle,
  surfaceScroll: stripe.surface,
  active: stripe.success,
  activeSoft: stripe.successSoft,
} as const;

export type StripeTokens = typeof stripe;
export type SemanticTokens = typeof semantic;

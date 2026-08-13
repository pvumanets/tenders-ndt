import { density } from "../../../theme/density";

import { stripe } from "../../../theme/palette";



/**

 * C-002 column header — три уровня (DevTools sign-off):

 * 1. title — 15px / 500 / #3C4257 / lh 1.25

 * 2. identity — 11px / 400 / #697386 / pt 7px

 * 3. strip — 11px / 400

 */



/** Орск, Межвахта, Запас, В дороге, Спецзадание */

export const columnHeaderTitleSx = {

  margin: 0,

  fontSize: 15,

  fontWeight: density.weight.medium,

  lineHeight: 1.25,

  color: stripe.text,

} as const;



/** «Свободный · Завод Свободный» */

export const columnHeaderIdentitySx = {

  display: "block",

  lineHeight: 1.3,

  pt: "7px",

  fontSize: density.font.xs,

  fontWeight: density.weight.regular,

  color: stripe.textMuted,

} as const;



/** Strip container caption */

export const columnHeaderStripSx = {

  fontSize: density.font.xs,

  fontWeight: density.weight.regular,

  lineHeight: 1.3,

} as const;



/** C-020 v2 — «3 / 12» fraction row */

export const columnMetricsFractionSx = {

  display: "flex",

  alignItems: "baseline",

  gap: 0.5,

  lineHeight: 1.3,

} as const;



export const columnMetricsAssignedSx = {

  fontSize: density.font.xs,

  fontWeight: density.weight.regular,

  lineHeight: 1.3,

} as const;



export const columnMetricsSlashSx = {

  fontSize: density.font.xs,

  fontWeight: density.weight.regular,

  color: stripe.textMuted,

  lineHeight: 1.3,

} as const;



export const columnMetricsPlanSx = {

  fontSize: density.font.xs,

  fontWeight: density.weight.regular,

  lineHeight: 1.3,

} as const;



/** «Устарело» рядом с числом плана */

export const columnMetricsStaleSx = {

  fontSize: density.font.xs,

  fontWeight: density.weight.regular,

  lineHeight: 1.3,

  color: stripe.textMuted,

  whiteSpace: "nowrap",

} as const;



/** Segmented progress bar — pill caps */

export const columnMetricsBarSx = {

  height: 5,

  borderRadius: 9999,

  overflow: "hidden",

  display: "flex",

  width: "100%",

  bgcolor: stripe.surfaceSubtle,

} as const;


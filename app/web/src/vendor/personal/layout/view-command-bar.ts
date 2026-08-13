import { density } from "../../../theme/density";

export const viewCommandBarLayout = {
  barMinHeight: density.toolbar.minHeight,
  groupGap: 1,
  outerGap: 1.5,
  separatorHeight: 20,
  /** Vertical breathing room inside the bar (not only minHeight). */
  paddingY: 1.5,
  /** Horizontal inset inside the bar (MUI 2.5 → 20px at spacing 8). */
  paddingX: 2.5,
  /** Match kanban columns (`BoardColumn` uses `density.radius.sm`). */
  borderRadius: density.radius.sm,
  /** Gap between command bar and content below (board, table). */
  marginBottom: 2,
} as const;

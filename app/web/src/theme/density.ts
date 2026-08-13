/** Unified compact scale — Stripe Dashboard density */
export const density = {
  font: {
    xs: 11,
    sm: 12,
    md: 13,
    lg: 14,
    xl: 16,
    xxl: 18,
    profile: 25,
  },
  weight: {
    regular: 400,
    medium: 500,
  },
  control: {
    sm: 28,
    md: 32,
    lg: 36,
  },
  chip: {
    height: 20,
    fontSize: 11,
  },
  input: {
    padding: "6px 10px",
  },
  button: {
    padding: "0 12px",
    radius: 6,
    /** Bitrix-style link on PersonMiniCard — font.xs, gap = personMiniCard.toAction */
    cardLink: {
      fontSize: 11,
      lineHeight: 1.2,
      padding: 0,
      sectionPaddingTop: 20,
    },
  },
  tab: {
    minHeight: 32,
  },
  toolbar: {
    minHeight: 48,
  },
  sidebar: {
    width: 220,
  },
  avatar: {
    sm: 28,
  },
  /** PersonMiniCard — fits «Овсянников · Деф.» + meta + 4 skill icons */
  card: {
    minWidth: 252,
  },
  /**
   * PersonMiniCard body blocks (C-001): Identity → Fact → Intent → Compliance → Action.
   * Same rhythm on «Сегодня» and «План на T».
   */
  personMiniCard: {
    /** Identity (avatar+ФИО) → Fact */
    headerToBody: 8,
    /** Fact (счётчики / прогноз) → Intent (стрелки) */
    factToIntent: 10,
    /** Fact or Intent → Compliance chips */
    toCompliance: 20,
    /** Compliance or body → Action footer */
    toAction: 20,
    /** Between rows inside Fact block */
    factRowGap: 2,
  },
  /** Kanban column = card.minWidth + horizontal padding (p: 1.25 × 2) */
  column: {
    paddingX: 10,
    minWidth: 272,
    maxWidthScroll: 300,
    maxWidthFixed: 288,
  },
  icon: {
    sm: 14,
    md: 16,
  },
  /** Checkbox, radio, switch — чуть меньше дефолта MUI */
  selection: {
    icon: 18,
    padding: 5,
  },
  radius: {
    sm: 6,
    md: 8,
    lg: 10,
  },
} as const;

export type DensityTokens = typeof density;

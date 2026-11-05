/** 4-pt spacing scale. Use these instead of ad-hoc numbers for padding, margins and gaps. */
export const spacing = {
  xxs: 4,
  xs: 8,
  sm: 12,
  md: 16,
  lg: 20,
  xl: 24,
  xxl: 32,
  xxxl: 40,
  huge: 56,
} as const;

/** Radii shared by every screen (design refresh 2026-11-05: calmer, less pill-heavy). */
export const radii = {
  /** Buttons and button-like actions (52 tall). */
  button: 14,
  field: 12,
  /** Static cards, rows and sections. */
  card: 16,
  /** Cards whose face is a photo. */
  photoCard: 20,
  /** Banners, notices, thumbnails and other inset surfaces. */
  inset: 12,
  iconTile: 10,
  /** Filter and choice chips, small status pills. */
  chip: 999,
  sheet: 28,
  pill: 999,
} as const;

/** Button height (design system). */
export const BUTTON_HEIGHT = 52;

/** Minimum touch target (WCAG / platform HIG). */
export const MIN_TOUCH = 44;

export type SpacingToken = keyof typeof spacing;

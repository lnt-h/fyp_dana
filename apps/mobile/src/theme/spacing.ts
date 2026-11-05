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

/** Radii shared by every screen (design system). */
export const radii = {
  action: 22,
  field: 17,
  card: 24,
  iconTile: 14,
  chip: 16,
  sheet: 40,
  pill: 999,
} as const;

/** Minimum touch target (WCAG / platform HIG). */
export const MIN_TOUCH = 44;

export type SpacingToken = keyof typeof spacing;

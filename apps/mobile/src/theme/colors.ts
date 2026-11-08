/**
 * Bright, photo-first palette (visual refresh 2026-11-09, docs/04-design/ui-ux/visual-refresh-2026-11-09.md).
 * White surfaces, near-black text, ONE brand colour (teal `primary`) for actions; categories and days carry colour.
 * Contrast ratios are WCAG 2.1 against white / surface (#F5F7F8). Text needs ≥ 4.5:1; icons and strokes ≥ 3:1.
 * Brand anchors kept for the logo only: deepOcean, sun.
 */
const palette = {
  canvas: '#FFFFFF',
  /** Grouped backgrounds, chips, skeletons, icon tiles. */
  surface: '#F5F7F8',
  hairline: '#E5E8EB',
  /** Text (16.3:1 white, 15.2:1 surface). */
  ink: '#16212B',
  /** Secondary text, section kickers (7.6:1 white, 7.1:1 surface). */
  textSecondary: '#4A5562',
  /** Captions, meta (4.74:1 white, 4.41:1 surface: below AA on surface, so muted text only on white). */
  textMuted: '#6B7480',
  /** Buttons, links, selected (5.18:1 white text on it; 4.82:1 as text on surface; 4.59:1 on primarySoft). */
  primary: '#0B7A75',
  primaryPressed: '#09625E',
  /** Selected chip background, soft fills. */
  primarySoft: '#E6F4F3',
  /** Fills, FAB, highlights only (white on it 3.62:1: icons or ≥ 19 pt bold text only). */
  coral: '#E8553D',
  /** Coral for text (5.14:1 white; 4.49:1 on coralSoft, so coral text sits on white). */
  coralText: '#C2412A',
  coralSoft: '#FDECE8',
  /** AI violet: ONLY the small sparkle mark (7.1:1 white). */
  ai: '#6D28D9',
  aiSoft: '#F3EEFE',
  /** Semantic pairs: strong text on its soft bg. success 4.57:1 · warning 6.37:1 · danger 5.30:1 · info 5.49:1. */
  success: '#15803D',
  successBg: '#DCFCE7',
  warning: '#92400E',
  warningBg: '#FEF3C7',
  danger: '#B91C1C',
  dangerBg: '#FEE2E2',
  info: '#1D4ED8',
  infoBg: '#DBEAFE',
  /** Brand mark only (logo, onboarding art). */
  deepOcean: '#0B3045',
  sun: '#F6A623',
  white: '#FFFFFF',
  disabledButton: '#A8B0B8',
} as const;

export const colors = {
  ...palette,
  // Legacy names (pre-2026-11-09 screens): remapped onto the new palette; prefer the semantic names above in new code.
  /** → textSecondary. */
  accentText: palette.textSecondary,
  /** → primary (fills and strokes). */
  audioTeal: palette.primary,
  /** → surface. */
  surfaceTint: palette.surface,
  /** → primary (text and links). */
  tealText: palette.primary,
  teal: palette.primary,
  tealDark: palette.primaryPressed,
  /** → coral (map pins, highlights; not for small text). */
  terracotta: palette.coral,
  /** → primarySoft (auth/onboarding art wash). */
  skyWash: palette.primarySoft,
  mutedDot: '#D5DADF',
  ok: palette.success,
  okBg: palette.successBg,
  warn: palette.warning,
  warnBg: palette.warningBg,
} as const;

/**
 * Day colours for pins, route lines and day chips: day 1 teal, day 2 coral, day 3 indigo (white on indigo 6.29:1).
 * Index wraps for safety; trips are 1–3 days.
 */
export const dayColors = [palette.primary, palette.coral, '#4F46E5'] as const;
/** Soft backgrounds for day chips. */
export const dayColorsSoft = [palette.primarySoft, palette.coralSoft, '#EEF2FF'] as const;
/**
 * Fill for numbered pins carrying a small white number: coral (3.62:1) is too light for 12–14 pt numbers, so day 2
 * pins use coralText (5.14:1). Route lines use `dayColors`.
 */
export const dayPinColors = [palette.primary, palette.coralText, '#4F46E5'] as const;

/** 0-based day index → day colour. */
export function dayColor(index: number): string {
  const n = dayColors.length;
  return dayColors[((Math.trunc(index) % n) + n) % n];
}

/** 0-based day index → pin fill (white number ≥ 4.5:1). */
export function dayPinColor(index: number): string {
  const n = dayPinColors.length;
  return dayPinColors[((Math.trunc(index) % n) + n) % n];
}

/** 0-based day index → soft day background. */
export function daySoftColor(index: number): string {
  const n = dayColorsSoft.length;
  return dayColorsSoft[((Math.trunc(index) % n) + n) % n];
}

export type CategoryTone = { fg: string; bg: string };

/**
 * Category colours, always paired with the category icon (tile = soft bg + strong icon). `fg` is for icons and
 * strokes (≥ 3:1 on bg except MARKET 2.74:1, which is decorative beside its icon), never for text: category labels
 * stay ink. fg on bg: HERITAGE 4.51 · RELIGIOUS_SITE 4.80 · MUSEUM 4.24 · VIEWPOINT 3.29 · NATURE 3.00 · BEACH 3.57 ·
 * THEME_PARK 3.91 · FOOD 3.11 · CAFE 6.37 · MARKET 2.74 · NIGHTLIFE 4.56 · CRAFT_VILLAGE 3.32.
 */
export const categoryColors: Record<string, CategoryTone> = {
  HERITAGE: { fg: '#B45309', bg: '#FEF3C7' },
  RELIGIOUS_SITE: { fg: '#7C3AED', bg: '#EDE9FE' },
  MUSEUM: { fg: '#2563EB', bg: '#DBEAFE' },
  VIEWPOINT: { fg: '#0891B2', bg: '#CFFAFE' },
  NATURE: { fg: '#16A34A', bg: '#DCFCE7' },
  BEACH: { fg: '#0284C7', bg: '#E0F2FE' },
  THEME_PARK: { fg: '#DB2777', bg: '#FCE7F3' },
  FOOD: { fg: '#EA580C', bg: '#FFEDD5' },
  CAFE: { fg: '#92400E', bg: '#FEF3C7' },
  MARKET: { fg: '#CA8A04', bg: '#FEF9C3' },
  NIGHTLIFE: { fg: '#9333EA', bg: '#F3E8FF' },
  CRAFT_VILLAGE: { fg: '#0D9488', bg: '#CCFBF1' },
};

const DEFAULT_CATEGORY: CategoryTone = { fg: palette.primary, bg: palette.primarySoft };

/** Fixture/legacy lower-case codes → contract codes (mirrors `normalizeCategoryCode` in components/ui/Icon). */
const LEGACY: Record<string, string> = { evening: 'NIGHTLIFE', history: 'HERITAGE', temple: 'RELIGIOUS_SITE' };

/** Category code (API UPPER_CASE or legacy lower-case) → colours; unknown or missing → primary. */
export function categoryColor(code?: string | null): CategoryTone {
  if (!code) return DEFAULT_CATEGORY;
  return categoryColors[LEGACY[code] ?? code.toUpperCase()] ?? DEFAULT_CATEGORY;
}

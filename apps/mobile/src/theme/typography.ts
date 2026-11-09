import type { TextStyle } from 'react-native';
import { colors } from './colors';

/** Hanken Grotesk weights loaded in the root layout: body 400, labels 500, titles 600/700. */
export const fonts = {
  regular: 'HankenGrotesk_400Regular',
  medium: 'HankenGrotesk_500Medium',
  semibold: 'HankenGrotesk_600SemiBold',
  bold: 'HankenGrotesk_700Bold',
} as const;

/**
 * Text presets (visual refresh 2026-11-09). Sentence case everywhere: no uppercase, no tracking on kickers.
 * Colours default to ink; override `color` per use (keep ≥ 4.5:1 contrast).
 */
export const typography = {
  display: { color: colors.ink, fontFamily: fonts.bold, fontSize: 30, letterSpacing: -0.6, lineHeight: 36 },
  title: { color: colors.ink, fontFamily: fonts.bold, fontSize: 24, letterSpacing: -0.4, lineHeight: 30 },
  headline: { color: colors.ink, fontFamily: fonts.semibold, fontSize: 19, letterSpacing: -0.2, lineHeight: 25 },
  body: { color: colors.ink, fontFamily: fonts.regular, fontSize: 16, lineHeight: 24 },
  bodyStrong: { color: colors.ink, fontFamily: fonts.semibold, fontSize: 16, lineHeight: 24 },
  label: { color: colors.ink, fontFamily: fonts.medium, fontSize: 15, lineHeight: 20 },
  caption: { color: colors.textMuted, fontFamily: fonts.regular, fontSize: 13, lineHeight: 18 },
  micro: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 12, lineHeight: 16 },
  /** Section kicker: sentence case, 13 semibold, textSecondary (7.6:1 on white). No uppercase, no tracking. */
  eyebrow: { color: colors.textSecondary, fontFamily: fonts.semibold, fontSize: 13, lineHeight: 18 },
} as const satisfies Record<string, TextStyle>;

export type TypographyToken = keyof typeof typography;

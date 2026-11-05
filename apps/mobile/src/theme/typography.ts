import type { TextStyle } from 'react-native';
import { colors } from './colors';

/** Hanken Grotesk weights loaded in the root layout: body 400, labels 500, titles 600/700. */
export const fonts = {
  regular: 'HankenGrotesk_400Regular',
  medium: 'HankenGrotesk_500Medium',
  semibold: 'HankenGrotesk_600SemiBold',
  bold: 'HankenGrotesk_700Bold',
} as const;

/** Text presets. Colours default to ink; override `color` per use (keep ≥4.5:1 contrast). */
export const typography = {
  display: { color: colors.ink, fontFamily: fonts.bold, fontSize: 34, letterSpacing: -0.8, lineHeight: 40 },
  title: { color: colors.ink, fontFamily: fonts.bold, fontSize: 28, letterSpacing: -0.5, lineHeight: 34 },
  headline: { color: colors.ink, fontFamily: fonts.semibold, fontSize: 20, letterSpacing: -0.2, lineHeight: 26 },
  body: { color: colors.ink, fontFamily: fonts.regular, fontSize: 16, lineHeight: 24 },
  bodyStrong: { color: colors.ink, fontFamily: fonts.semibold, fontSize: 16, lineHeight: 24 },
  caption: { color: colors.textMuted, fontFamily: fonts.regular, fontSize: 13, lineHeight: 18 },
  label: { color: colors.ink, fontFamily: fonts.regular, fontSize: 15, letterSpacing: 0.1, lineHeight: 20 },
  /** Section kicker: small caps in accentText (6.7:1 on canvas). Replaces pill badges above titles. */
  eyebrow: { color: colors.accentText, fontFamily: fonts.semibold, fontSize: 11, letterSpacing: 1.6, lineHeight: 14, textTransform: 'uppercase' },
} as const satisfies Record<string, TextStyle>;

export type TypographyToken = keyof typeof typography;

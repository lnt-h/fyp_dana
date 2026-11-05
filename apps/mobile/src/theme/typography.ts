import type { TextStyle } from 'react-native';
import { colors } from './colors';

export const fonts = {
  medium: 'HankenGrotesk_500Medium',
  bold: 'HankenGrotesk_700Bold',
} as const;

/** Text presets. Colours default to ink; override `color` per use (keep ≥4.5:1 contrast). */
export const typography = {
  display: { color: colors.ink, fontFamily: fonts.bold, fontSize: 34, letterSpacing: -0.8, lineHeight: 40 },
  title: { color: colors.ink, fontFamily: fonts.bold, fontSize: 28, letterSpacing: -0.5, lineHeight: 34 },
  headline: { color: colors.ink, fontFamily: fonts.bold, fontSize: 20, letterSpacing: -0.2, lineHeight: 26 },
  body: { color: colors.ink, fontFamily: fonts.medium, fontSize: 16, lineHeight: 24 },
  bodyStrong: { color: colors.ink, fontFamily: fonts.bold, fontSize: 16, lineHeight: 24 },
  caption: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18 },
  label: { color: colors.ink, fontFamily: fonts.bold, fontSize: 15, letterSpacing: 0.1, lineHeight: 20 },
} as const satisfies Record<string, TextStyle>;

export type TypographyToken = keyof typeof typography;

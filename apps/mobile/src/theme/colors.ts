/**
 * Warm, local palette (design refresh 2026-11-05). Contrast ratios are WCAG 2.1 against white / canvas / surfaceTint.
 * Brand anchors from onboarding and auth stay: deepOcean, sun (logo dot), ink.
 */
export const colors = {
  /** Brick-brown accent for text: eyebrows and kickers (7.1:1 white, 6.7:1 canvas, 6.2:1 surfaceTint). */
  accentText: '#8A4513',
  /** Fill and stroke only (selected states, progress). Not for text. */
  audioTeal: '#00839C',
  /** Warm paper page background. */
  canvas: '#FBF7F0',
  danger: '#A43A2E',
  dangerBg: '#F9E6E2',
  deepOcean: '#0B3045',
  disabledButton: '#A8A8A8',
  /** Hairline borders and dividers on static cards (decorative, not a control boundary). */
  hairline: '#E6DFD2',
  ink: '#07151E',
  mutedDot: '#D4E0E5',
  ok: '#1B6F5F',
  okBg: '#E3F1EC',
  /** Cool wash kept only for the owner's auth/onboarding art. App surfaces use surfaceTint. */
  skyWash: '#E8F5F7',
  sun: '#F6A623',
  /** Warm tint for icon tiles, chips, segmented controls, skeletons and photo placeholders. */
  surfaceTint: '#F4EEE3',
  teal: '#28B6B5',
  tealDark: '#0B8EA8',
  /** Teal for text and links (5.14:1 white, 4.82:1 canvas; 4.45:1 on surfaceTint, so never text there). Use audioTeal only for fills and strokes. */
  tealText: '#00788F',
  /** Map pins and the active stop; white text on it only at ≥15 pt bold (4.85:1). */
  terracotta: '#B8541F',
  /** Warm muted body text (6.8:1 white, 6.4:1 canvas, 5.9:1 surfaceTint). */
  textMuted: '#5F5A52',
  warn: '#7A4E00',
  warnBg: '#FFF1D6',
  white: '#FFFFFF',
} as const;

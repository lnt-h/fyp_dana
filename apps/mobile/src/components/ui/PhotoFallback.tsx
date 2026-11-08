import { LinearGradient } from 'expo-linear-gradient';
import { StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { categoryColor, colors } from '../../theme/colors';
import { fonts } from '../../theme/typography';
import { Icon, categoryIcon, normalizeCategoryCode, type IconName } from './Icon';

/** Gradient stops and glyph colour for one category; `deep` carries white glyphs, `light` carries the category colour. */
type Swatch = { deep: readonly [string, string]; light: readonly [string, string]; ink: string };

/** Blend two #RRGGBB colours (t = 0 → a, 1 → b). */
function mix(a: string, b: string, t: number): string {
  const ch = (hex: string, i: number) => parseInt(hex.slice(1 + i * 2, 3 + i * 2), 16);
  return `#${[0, 1, 2].map(i => Math.round(ch(a, i) + (ch(b, i) - ch(a, i)) * t).toString(16).padStart(2, '0')).join('')}`;
}

const swatches = new Map<string, Swatch>();

/**
 * Category colours (theme `categoryColor`, unknown → primary teal). `light` = the category's soft colour deepening
 * slightly toward its strong colour, glyph in the strong colour. `deep` = the strong colour shaded toward ink, for
 * photo cards and heroes that overlay white text on their own scrim.
 */
function swatchFor(categoryCode: string | null | undefined): Swatch {
  const { fg, bg } = categoryColor(normalizeCategoryCode(categoryCode));
  const key = fg + bg;
  let swatch = swatches.get(key);
  if (!swatch) {
    swatch = { deep: [mix(fg, colors.ink, 0.35), mix(fg, colors.white, 0.08)], ink: fg, light: [mix(bg, colors.white, 0.4), mix(bg, fg, 0.18)] };
    swatches.set(key, swatch);
  }
  return swatch;
}

/** First letter or digit of a name (NFC, so "Đà" → "Đ"), upper-cased; null when there is none. */
export function placeInitial(name: string | null | undefined): string | null {
  if (!name) return null;
  const letter = Array.from(name.normalize('NFC')).find(ch => ch.toLowerCase() !== ch.toUpperCase() || /[0-9]/.test(ch));
  return letter ? letter.toLocaleUpperCase() : null;
}

export type PhotoFallbackProps = {
  /** Category code of the place (`HERITAGE`, `FOOD`, …): picks the tile colour and, unless `icon` is set, its icon. */
  categoryCode?: string | null;
  /** Place name: its initial is drawn on the tile. */
  name?: string | null;
  /** Icon override (cities, trips); default = the category icon, or the map pin. */
  icon?: IconName;
  iconSize?: number;
  /**
   * `light` (default) = soft category gradient with the glyph in the category colour (thumbnails, place hero).
   * `dark` = strong category gradient with a white glyph, for photo cards that overlay white text.
   */
  tone?: 'light' | 'dark';
  /**
   * `tile` (default): icon centred, large faint initial on the right (cards, heroes).
   * `thumb`: the initial centred with a small category badge (≤ 72 pt thumbnails); icon only when there is no name.
   */
  variant?: 'tile' | 'thumb';
  /** Gradient only, no glyphs: the loading placeholder under a remote photo. */
  bare?: boolean;
  style?: StyleProp<ViewStyle>;
};

/**
 * Deterministic stand-in when a place, city or trip has no photo (or its photo failed to load): a category-tinted
 * gradient with the category icon and the place's initial. Fills its parent; decorative (the card names the place).
 */
export function PhotoFallback({ categoryCode, name, icon, iconSize = 28, tone = 'light', variant = 'tile', bare = false, style }: PhotoFallbackProps) {
  const swatch = swatchFor(categoryCode);
  const dark = tone === 'dark';
  const glyph = dark ? 'rgba(255,255,255,0.86)' : swatch.ink;
  const glyphName = icon ?? categoryIcon(categoryCode);
  const initial = placeInitial(name);

  let content = null;
  if (!bare && variant === 'thumb') {
    content = initial
      ? <>
          <Text allowFontScaling={false} style={[styles.thumbInitial, { color: glyph, fontSize: Math.round(iconSize * 0.95), lineHeight: Math.round(iconSize * 1.15) }]}>{initial}</Text>
          <View style={[styles.badge, { backgroundColor: dark ? 'rgba(255,255,255,0.18)' : 'rgba(255,255,255,0.7)' }]}>
            <Icon color={glyph} name={glyphName} size={12} strokeWidth={2} />
          </View>
        </>
      : <Icon color={glyph} name={glyphName} size={iconSize} />;
  } else if (!bare) {
    content = <>
      {initial ? <Text allowFontScaling={false} style={[styles.watermark, { color: dark ? 'rgba(255,255,255,0.12)' : swatch.ink, opacity: dark ? 1 : 0.1 }]}>{initial}</Text> : null}
      <View style={[styles.iconRing, { backgroundColor: dark ? 'rgba(255,255,255,0.14)' : 'rgba(255,255,255,0.7)', height: iconSize * 2, width: iconSize * 2, borderRadius: iconSize }]}>
        <Icon color={glyph} name={glyphName} size={iconSize} />
      </View>
    </>;
  }

  return (
    <View
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      pointerEvents="none"
      style={[StyleSheet.absoluteFill, styles.base, style]}
    >
      <LinearGradient colors={dark ? swatch.deep : swatch.light} end={{ x: 1, y: 1 }} start={{ x: 0, y: 0 }} style={StyleSheet.absoluteFill} />
      {/* Soft highlight in the top-left corner so a flat tile reads as a lit surface, not an empty box. */}
      <View style={[styles.sheen, { backgroundColor: dark ? 'rgba(255,255,255,0.07)' : 'rgba(255,255,255,0.45)' }]} />
      {content}
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { alignItems: 'center', borderRadius: 9, bottom: 4, height: 18, justifyContent: 'center', position: 'absolute', right: 4, width: 18 },
  base: { alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  iconRing: { alignItems: 'center', justifyContent: 'center' },
  sheen: { borderRadius: 999, height: '90%', left: '-25%', position: 'absolute', top: '-45%', width: '90%' },
  thumbInitial: { fontFamily: fonts.bold, includeFontPadding: false, textAlign: 'center' },
  watermark: { bottom: -28, fontFamily: fonts.bold, fontSize: 150, includeFontPadding: false, lineHeight: 160, position: 'absolute', right: -6 },
});

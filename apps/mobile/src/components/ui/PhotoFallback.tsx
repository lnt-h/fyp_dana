import { LinearGradient } from 'expo-linear-gradient';
import { StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { fonts } from '../../theme/typography';
import { Icon, categoryIcon, type IconName } from './Icon';

/** Gradient stops and glyph colour for one category family; `deep` carries white text, `light` carries `ink`. */
type Swatch = { deep: readonly [string, string]; light: readonly [string, string]; ink: string };

/**
 * One swatch per category icon family (`categoryIcon`), so a tile's colour says what kind of place it is. Deep stops
 * keep white glyphs ≥ 4.5:1 at the darker end; card text always sits on the card's own scrim on top of this.
 */
const SWATCHES: Record<string, Swatch> = {
  beach: { deep: ['#005A6E', '#1B8FA5'], ink: '#00687D', light: ['#E2F2F5', '#C8E6ED'] },
  food: { deep: ['#86291F', '#B95436'], ink: '#9A3328', light: ['#FAE7E1', '#F2CFC4'] },
  heritage: { deep: ['#6E3410', '#A9501E'], ink: '#8A4513', light: ['#F7E8DB', '#EED6C2'] },
  lantern: { deep: ['#20264F', '#463A78'], ink: '#3A3570', light: ['#E8E7F3', '#D6D3EA'] },
  market: { deep: ['#634000', '#9C6A0E'], ink: '#7A4E00', light: ['#FBF0D9', '#F2DEB4'] },
  nature: { deep: ['#11524A', '#277F67'], ink: '#1B6F5F', light: ['#E2F1EB', '#CBE5DA'] },
  sparkle: { deep: ['#552A62', '#8A4A82'], ink: '#6E3A78', light: ['#F2E5F0', '#E6CFE3'] },
};
const DEFAULT_SWATCH: Swatch = { deep: ['#0B3045', '#1D566F'], ink: '#5F5A52', light: ['#F4EEE3', '#EAE0CF'] };

function swatchFor(categoryCode: string | null | undefined): Swatch {
  return SWATCHES[categoryIcon(categoryCode)] ?? DEFAULT_SWATCH;
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
   * `light` (default) = pale category wash with a coloured glyph, for thumbnails without text on top.
   * `dark` = deep category gradient, for photo cards that overlay white text.
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
      <View style={[styles.iconRing, { backgroundColor: dark ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.55)', height: iconSize * 2, width: iconSize * 2, borderRadius: iconSize }]}>
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

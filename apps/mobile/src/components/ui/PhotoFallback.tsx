import { StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors } from '../../theme/colors';
import { Icon, categoryIcon, type IconName } from './Icon';

/** First letter or digit of a name (NFC, so "Đà" → "Đ"), upper-cased; null when there is none. */
export function placeInitial(name: string | null | undefined): string | null {
  if (!name) return null;
  const letter = Array.from(name.normalize('NFC')).find(ch => ch.toLowerCase() !== ch.toUpperCase() || /[0-9]/.test(ch));
  return letter ? letter.toLocaleUpperCase() : null;
}

export type PhotoFallbackProps = {
  /** Category code of the place (`HERITAGE`, `FOOD`, …): picks the tile colour and, unless `icon` is set, its icon. */
  categoryCode?: string | null;
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
 * Deterministic neutral stand-in when a place, city or trip has no photo (or its photo failed to load):
 * an elegant neutral surface tile with a small centered category icon.
 * Follows the Anti-AI-slop rule: no giant watermark letters, no saturated rainbow gradients.
 */
export function PhotoFallback({ categoryCode, icon, iconSize = 24, tone = 'light', variant = 'tile', bare = false, style }: PhotoFallbackProps) {
  const dark = tone === 'dark';
  const glyphName = icon ?? categoryIcon(categoryCode);
  const glyphColor = dark ? 'rgba(255, 255, 255, 0.85)' : colors.textSecondary;
  const isThumb = variant === 'thumb';
  const effectiveIconSize = isThumb ? Math.min(iconSize, 18) : iconSize;

  return (
    <View
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      pointerEvents="none"
      style={[
        StyleSheet.absoluteFill,
        styles.base,
        { backgroundColor: dark ? '#1E262E' : '#EDEFF1' },
        style,
      ]}
    >
      {!bare && (
        <View
          style={[
            styles.iconRing,
            {
              backgroundColor: dark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(255, 255, 255, 0.85)',
              borderRadius: isThumb ? 10 : Math.round(effectiveIconSize * 0.9),
              height: isThumb ? 28 : Math.round(effectiveIconSize * 1.8),
              width: isThumb ? 28 : Math.round(effectiveIconSize * 1.8),
            },
          ]}
        >
          <Icon color={glyphColor} name={glyphName} size={effectiveIconSize} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  base: { alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  iconRing: { alignItems: 'center', justifyContent: 'center' },
});

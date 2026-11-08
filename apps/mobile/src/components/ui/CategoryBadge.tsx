import { StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { categoryColor, colors } from '../../theme/colors';
import { radii } from '../../theme/spacing';
import { fonts } from '../../theme/typography';
import { Icon, categoryIcon, normalizeCategoryCode } from './Icon';

export type CategoryBadgeProps = {
  /** Category code (`HERITAGE`, `FOOD`, …; legacy lower-case accepted). Unknown → primary teal and the map pin. */
  code?: string | null;
  /** Localized category name. Spoken for the tile; shown as text for the chip. */
  label: string;
  /** `tile` = square icon tile (default 40); `chip` = inline pill with icon + label (28 tall). */
  variant?: 'tile' | 'chip';
  /** Tile edge in dp (default 40). */
  size?: number;
  style?: StyleProp<ViewStyle>;
};

/** Category colour + icon. Colour is always paired with the icon; label text stays ink (category colours are icon-only). */
export function CategoryBadge({ code, label, variant = 'tile', size = 40, style }: CategoryBadgeProps) {
  const normalized = normalizeCategoryCode(code);
  const { fg, bg } = categoryColor(normalized);
  const icon = categoryIcon(normalized);
  if (variant === 'chip') {
    return (
      <View accessible accessibilityLabel={label} style={[styles.chip, { backgroundColor: bg }, style]}>
        <Icon color={fg} name={icon} size={14} strokeWidth={2} />
        <Text maxFontSizeMultiplier={1.3} numberOfLines={1} style={styles.chipText}>{label}</Text>
      </View>
    );
  }
  return (
    <View
      accessible
      accessibilityLabel={label}
      accessibilityRole="image"
      style={[styles.tile, { backgroundColor: bg, borderRadius: Math.round(size * 0.3), height: size, width: size }, style]}
    >
      <Icon color={fg} name={icon} size={Math.round(size * 0.55)} strokeWidth={2} />
    </View>
  );
}

const styles = StyleSheet.create({
  chip: { alignItems: 'center', alignSelf: 'flex-start', borderRadius: radii.pill, flexDirection: 'row', gap: 5, minHeight: 28, paddingHorizontal: 10 },
  chipText: { color: colors.ink, flexShrink: 1, fontFamily: fonts.semibold, fontSize: 13, lineHeight: 17 },
  tile: { alignItems: 'center', justifyContent: 'center' },
});

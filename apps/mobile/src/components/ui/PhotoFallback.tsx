import { StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors } from '../../theme/colors';
import { Icon, type IconName } from './Icon';

export type PhotoFallbackProps = {
  /** Category icon (see `categoryIcon`); default map pin. */
  icon?: IconName;
  iconSize?: number;
  /**
   * `light` (default) = surfaceTint with a muted icon, for thumbnails without text on top.
   * `dark` = flat deepOcean, for photo cards that overlay white text (keeps that text ≥4.5:1 without a photo).
   */
  tone?: 'light' | 'dark';
  style?: StyleProp<ViewStyle>;
};

/** Flat stand-in when a place or city has no photo. Fills its parent; decorative. */
export function PhotoFallback({ icon = 'map-pin', iconSize = 28, tone = 'light', style }: PhotoFallbackProps) {
  const dark = tone === 'dark';
  return (
    <View
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={[StyleSheet.absoluteFill, styles.base, { backgroundColor: dark ? colors.deepOcean : colors.surfaceTint }, style]}
    >
      <Icon color={dark ? 'rgba(255,255,255,0.55)' : colors.textMuted} name={icon} size={iconSize} />
    </View>
  );
}

const styles = StyleSheet.create({
  base: { alignItems: 'center', justifyContent: 'center' },
});

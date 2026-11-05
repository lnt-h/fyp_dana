import { Pressable, StyleSheet, type StyleProp, type ViewStyle } from 'react-native';
import { colors } from '../../theme/colors';
import { elevation } from '../../theme/elevation';
import { Icon, type IconName } from './Icon';

export type CircleButtonProps = {
  icon: IconName;
  /** Required: icon-only buttons need a spoken name. */
  accessibilityLabel: string;
  onPress: () => void;
  /** Diameter 44–48 (default 46). */
  size?: 44 | 46 | 48;
  /** `light` = white circle for use over photos/maps; `tint` = surfaceTint circle on white surfaces. */
  tone?: 'light' | 'tint';
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
};

export function CircleButton({ icon, accessibilityLabel, onPress, size = 46, tone = 'light', disabled, style }: CircleButtonProps) {
  return (
    <Pressable
      accessibilityLabel={accessibilityLabel}
      accessibilityRole="button"
      accessibilityState={{ disabled: !!disabled }}
      disabled={disabled}
      hitSlop={4}
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        tone === 'light' ? [styles.light, elevation.md] : styles.tint,
        { borderRadius: size / 2, height: size, width: size },
        pressed && styles.pressed,
        disabled && styles.disabled,
        style,
      ]}
    >
      <Icon color={colors.ink} name={icon} size={22} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: { alignItems: 'center', justifyContent: 'center' },
  disabled: { opacity: 0.45 },
  light: { backgroundColor: colors.white },
  pressed: { opacity: 0.8, transform: [{ scale: 0.96 }] },
  tint: { backgroundColor: colors.surfaceTint },
});

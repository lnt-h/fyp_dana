import { LinearGradient } from 'expo-linear-gradient';
import { ActivityIndicator, Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors } from '../../theme/colors';
import { elevation } from '../../theme/elevation';
import { fonts } from '../../theme/typography';
import { Icon, type IconName } from './Icon';

const border = '#DCE8EE';

type BaseButtonProps = {
  label: string;
  onPress: () => void;
  icon?: IconName;
  /** Icon after the label (e.g. chevron-right) instead of before. */
  iconPosition?: 'start' | 'end';
  disabled?: boolean;
  /** Shows a spinner, keeps the width, blocks presses and sets accessibilityState.busy. */
  loading?: boolean;
  accessibilityLabel?: string;
  accessibilityHint?: string;
  style?: StyleProp<ViewStyle>;
};

export type PrimaryButtonProps = BaseButtonProps & {
  /** `ink` = solid ink pill (default); `gradient` = audioTeal→deepOcean. */
  variant?: 'ink' | 'gradient';
};

function Content({ label, icon, iconPosition = 'start', loading, color }: Pick<BaseButtonProps, 'label' | 'icon' | 'iconPosition' | 'loading'> & { color: string }) {
  return (
    <View style={styles.content}>
      <View style={[styles.content, loading && styles.hidden]}>
        {icon && iconPosition === 'start' ? <Icon color={color} name={icon} size={20} /> : null}
        <Text numberOfLines={1} style={[styles.label, { color }]}>{label}</Text>
        {icon && iconPosition === 'end' ? <Icon color={color} name={icon} size={20} /> : null}
      </View>
      {loading ? <ActivityIndicator color={color} style={StyleSheet.absoluteFill} /> : null}
    </View>
  );
}

/** Pill CTA, height 60 / radius 30. */
export function PrimaryButton({ variant = 'ink', disabled, loading, onPress, style, accessibilityLabel, accessibilityHint, ...content }: PrimaryButtonProps) {
  const inactive = disabled || loading;
  return (
    <Pressable
      accessibilityHint={accessibilityHint}
      accessibilityLabel={accessibilityLabel ?? content.label}
      accessibilityRole="button"
      accessibilityState={{ busy: !!loading, disabled: !!disabled }}
      disabled={inactive}
      onPress={onPress}
      style={({ pressed }) => [styles.primary, !disabled && elevation.md, disabled && styles.disabledFill, pressed && styles.pressed, style]}
    >
      {variant === 'gradient' && !disabled ? (
        <LinearGradient colors={[colors.audioTeal, colors.deepOcean]} end={{ x: 1, y: 1 }} start={{ x: 0, y: 0 }} style={[StyleSheet.absoluteFill, styles.radius]} />
      ) : null}
      <Content {...content} color={colors.white} loading={loading} />
    </Pressable>
  );
}

/** Outline pill on white, same geometry as PrimaryButton. */
export function SecondaryButton({ disabled, loading, onPress, style, accessibilityLabel, accessibilityHint, ...content }: BaseButtonProps) {
  return (
    <Pressable
      accessibilityHint={accessibilityHint}
      accessibilityLabel={accessibilityLabel ?? content.label}
      accessibilityRole="button"
      accessibilityState={{ busy: !!loading, disabled: !!disabled }}
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [styles.secondary, disabled && styles.disabled, pressed && styles.pressedSecondary, style]}
    >
      <Content {...content} color={colors.ink} loading={loading} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  content: { alignItems: 'center', flexDirection: 'row', gap: 8, justifyContent: 'center' },
  disabled: { opacity: 0.45 },
  disabledFill: { backgroundColor: colors.disabledButton },
  hidden: { opacity: 0 },
  label: { fontFamily: fonts.bold, fontSize: 17, letterSpacing: 0.1 },
  pressed: { opacity: 0.88, transform: [{ scale: 0.99 }] },
  pressedSecondary: { backgroundColor: colors.skyWash },
  primary: { alignItems: 'center', backgroundColor: colors.ink, borderRadius: 30, height: 60, justifyContent: 'center', paddingHorizontal: 28 },
  radius: { borderRadius: 30 },
  secondary: {
    alignItems: 'center',
    backgroundColor: colors.white,
    borderColor: border,
    borderRadius: 30,
    borderWidth: 1.5,
    height: 60,
    justifyContent: 'center',
    paddingHorizontal: 28,
  },
});

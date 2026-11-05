import { ActivityIndicator, Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors } from '../../theme/colors';
import { BUTTON_HEIGHT, radii } from '../../theme/spacing';
import { fonts } from '../../theme/typography';
import { Icon, type IconName } from './Icon';

type BaseButtonProps = {
  label: string;
  onPress: () => void;
  icon?: IconName;
  /** Icon after the label (e.g. chevron-right) instead of before. */
  iconPosition?: 'start' | 'end';
  /** Icon size in dp (default 20). */
  iconSize?: number;
  disabled?: boolean;
  /** Shows a spinner, keeps the width, blocks presses and sets accessibilityState.busy. */
  loading?: boolean;
  accessibilityLabel?: string;
  accessibilityHint?: string;
  style?: StyleProp<ViewStyle>;
};

export type PrimaryButtonProps = BaseButtonProps;

type ContentProps = Pick<BaseButtonProps, 'label' | 'icon' | 'iconPosition' | 'iconSize' | 'loading'> & { color: string };

function Content({ label, icon, iconPosition = 'start', iconSize = 20, loading, color }: ContentProps) {
  return (
    <View style={styles.content}>
      <View style={[styles.content, loading && styles.hidden]}>
        {icon && iconPosition === 'start' ? <Icon color={color} name={icon} size={iconSize} /> : null}
        <Text maxFontSizeMultiplier={1.4} numberOfLines={1} style={[styles.label, { color }]}>{label}</Text>
        {icon && iconPosition === 'end' ? <Icon color={color} name={icon} size={iconSize} /> : null}
      </View>
      {loading ? <ActivityIndicator color={color} style={StyleSheet.absoluteFill} /> : null}
    </View>
  );
}

/** Solid ink CTA, 52 tall, radius 14. No gradient, no shadow. */
export function PrimaryButton({ disabled, loading, onPress, style, accessibilityLabel, accessibilityHint, ...content }: PrimaryButtonProps) {
  const inactive = disabled || loading;
  return (
    <Pressable
      accessibilityHint={accessibilityHint}
      accessibilityLabel={accessibilityLabel ?? content.label}
      accessibilityRole="button"
      accessibilityState={{ busy: !!loading, disabled: !!disabled }}
      disabled={inactive}
      onPress={onPress}
      style={({ pressed }) => [styles.primary, disabled && styles.disabledFill, pressed && styles.pressed, style]}
    >
      <Content {...content} color={colors.white} loading={loading} />
    </Pressable>
  );
}

/** Outline button on white, same geometry as PrimaryButton. */
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
  label: { fontFamily: fonts.semibold, fontSize: 16, letterSpacing: 0.1 },
  pressed: { opacity: 0.88 },
  pressedSecondary: { backgroundColor: colors.surfaceTint },
  primary: { alignItems: 'center', backgroundColor: colors.ink, borderRadius: radii.button, height: BUTTON_HEIGHT, justifyContent: 'center', paddingHorizontal: 24 },
  secondary: {
    alignItems: 'center',
    backgroundColor: colors.white,
    borderColor: colors.hairline,
    borderRadius: radii.button,
    borderWidth: 1.5,
    height: BUTTON_HEIGHT,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
});

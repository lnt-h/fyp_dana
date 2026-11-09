import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors } from '../../theme/colors';
import { radii } from '../../theme/spacing';
import { fonts } from '../../theme/typography';
import { Icon, type IconName } from './Icon';

export type StatusTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

const TONES: Record<StatusTone, { fg: string; bg: string; icon: IconName }> = {
  danger: { bg: colors.dangerBg, fg: colors.danger, icon: 'blocked' },
  info: { bg: colors.infoBg, fg: colors.info, icon: 'info' },
  neutral: { bg: colors.surface, fg: colors.textSecondary, icon: 'info' },
  success: { bg: colors.successBg, fg: colors.success, icon: 'check' },
  warning: { bg: colors.warningBg, fg: colors.warning, icon: 'warning' },
};

export type StatusPillProps = {
  tone: StatusTone;
  label: string;
  /** Leading icon; default per tone (check / warning / blocked / info). Pass `null` for none. */
  icon?: IconName | null;
  /** When set the pill is a button (e.g. Plan Health pill opens the health detail) and shows a chevron. */
  onPress?: () => void;
  accessibilityLabel?: string;
  accessibilityHint?: string;
  style?: StyleProp<ViewStyle>;
};

/** Soft-background status pill with strong text (all tones ≥ 4.5:1), 32 tall. E.g. Plan Health "Looks good" / "2 to check". */
export function StatusPill({ tone, label, icon, onPress, accessibilityLabel, accessibilityHint, style }: StatusPillProps) {
  const t = TONES[tone];
  const iconName = icon === null ? null : icon ?? t.icon;
  const body = (
    <>
      {iconName ? <Icon color={t.fg} name={iconName} size={16} strokeWidth={2} /> : null}
      <Text maxFontSizeMultiplier={1.4} numberOfLines={1} style={[styles.text, { color: t.fg }]}>{label}</Text>
      {onPress ? <Icon color={t.fg} name="chevron-right" size={14} strokeWidth={2.2} /> : null}
    </>
  );
  const look = [styles.pill, { backgroundColor: t.bg }, style];
  if (!onPress) return <View accessible accessibilityLabel={accessibilityLabel ?? label} style={look}>{body}</View>;
  return (
    <Pressable
      accessibilityHint={accessibilityHint}
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityRole="button"
      hitSlop={6}
      onPress={onPress}
      style={({ pressed }) => [look, pressed && styles.pressed]}
    >
      {body}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  pill: { alignItems: 'center', alignSelf: 'flex-start', borderRadius: radii.pill, flexDirection: 'row', gap: 6, minHeight: 32, paddingHorizontal: 12 },
  pressed: { opacity: 0.75 },
  text: { flexShrink: 1, fontFamily: fonts.semibold, fontSize: 14, lineHeight: 18 },
});

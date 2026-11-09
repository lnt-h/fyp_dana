import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors } from '../../theme/colors';
import { elevation } from '../../theme/elevation';
import { radii, spacing } from '../../theme/spacing';
import { fonts } from '../../theme/typography';
import { Icon, type IconName } from './Icon';

export type ToastProps = {
  text: string;
  /** Leading icon colour/default icon: success = check, info = info, neutral = none. */
  tone?: 'success' | 'info' | 'neutral';
  icon?: IconName;
  /** Shows a close button when set. Auto-hide timing stays with the caller. */
  onDismiss?: () => void;
  style?: StyleProp<ViewStyle>;
};

const ICON: Record<NonNullable<ToastProps['tone']>, { name?: IconName; color: string }> = {
  info: { color: '#93C5FD', name: 'info' },
  neutral: { color: colors.white },
  success: { color: '#86EFAC', name: 'check' },
};

/**
 * Short, non-modal confirmation (e.g. "Trip saved"): ink pill with white text (16.3:1), announced politely.
 * The pill always renders below a standard 44-pt navigation bar: callers anchor this near the top of the screen
 * (where the Back button sits) and the inner offset keeps the pill from ever covering back navigation.
 */
export function Toast({ text, tone = 'neutral', icon, onDismiss, style }: ToastProps) {
  const { t } = useTranslation();
  const look = ICON[tone];
  const iconName = icon ?? look.name;
  return (
    <View pointerEvents="box-none" style={style}>
    <View accessibilityLiveRegion="polite" accessibilityRole="alert" pointerEvents="box-none" style={[styles.toast, styles.belowNav, elevation.floating]}>
      {iconName ? <Icon color={look.color} name={iconName} size={18} strokeWidth={2} /> : null}
      <Text maxFontSizeMultiplier={1.4} style={styles.text}>{text}</Text>
      {onDismiss ? (
        <Pressable accessibilityLabel={t('common.dismiss')} accessibilityRole="button" hitSlop={10} onPress={onDismiss}>
          <Icon color={colors.white} name="close" size={16} strokeWidth={2} />
        </Pressable>
      ) : null}
    </View>
    </View>
  );
}

const styles = StyleSheet.create({
  text: { color: colors.white, flexShrink: 1, fontFamily: fonts.medium, fontSize: 15, lineHeight: 20 },
  toast: {
    alignItems: 'center',
    alignSelf: 'center',
    backgroundColor: colors.ink,
    borderRadius: radii.pill,
    flexDirection: 'row',
    gap: spacing.xs,
    maxWidth: 520,
    minHeight: 44,
    paddingHorizontal: spacing.md,
    paddingVertical: 10,
  },
  /** Standard snackbar clearance below a 44-pt nav bar: the pill never covers Back. */
  belowNav: { marginTop: 44 + spacing.xs },
});

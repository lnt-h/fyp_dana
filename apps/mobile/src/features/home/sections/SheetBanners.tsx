import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon, type IconName } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

/** Error text on white (6.1:1), same as SCR-031. */
const errorText = '#AF3434';

/** Inline error banner with a retry link (S-1). */
export function ErrorBanner({ message, retryLabel, onRetry }: { message: string; retryLabel: string; onRetry: () => void }) {
  return (
    <View accessibilityRole="alert" style={styles.error}>
      <Icon color={errorText} name="warning" size={20} />
      <Text style={styles.errorText}>{message}</Text>
      <Pressable accessibilityRole="button" hitSlop={4} onPress={onRetry} style={({ pressed }) => [styles.retry, pressed && styles.pressed]}>
        <Text style={styles.link}>{retryLabel}</Text>
      </Pressable>
    </View>
  );
}

/** Calm skyWash notice (offline, info). */
export function NoticeBanner({ message, icon = 'info' }: { message: string; icon?: IconName }) {
  return (
    <View accessibilityLiveRegion="polite" accessibilityRole="alert" style={styles.notice}>
      <Icon color={colors.tealText} name={icon} size={20} />
      <Text style={styles.noticeText}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  error: { alignItems: 'center', backgroundColor: colors.white, borderColor: '#F1D3D3', borderRadius: radii.chip, borderWidth: 1, flexDirection: 'row', gap: spacing.sm, paddingLeft: spacing.md },
  errorText: { color: errorText, flex: 1, fontFamily: fonts.medium, fontSize: 15, lineHeight: 21, paddingVertical: spacing.sm },
  link: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 15 },
  notice: { alignItems: 'center', backgroundColor: colors.skyWash, borderRadius: radii.chip, flexDirection: 'row', gap: spacing.sm, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  noticeText: { color: colors.ink, flex: 1, fontFamily: fonts.medium, fontSize: 14, lineHeight: 20 },
  pressed: { opacity: 0.7 },
  retry: { alignItems: 'center', justifyContent: 'center', minHeight: MIN_TOUCH, paddingHorizontal: spacing.md },
});

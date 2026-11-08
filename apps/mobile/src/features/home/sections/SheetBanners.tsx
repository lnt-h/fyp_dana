import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon, type IconName } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

/** Error text on white (6.1:1), same as SCR-031. */
const errorText = colors.danger;

/** Inline error banner with a retry link (S-1). `detail` is an optional second line (e.g. why: offline, busy). */
export function ErrorBanner({ message, detail, retryLabel, onRetry }: { message: string; detail?: string | null; retryLabel: string; onRetry: () => void }) {
  return (
    <View accessibilityRole="alert" style={styles.error}>
      <Icon color={errorText} name="warning" size={20} />
      <View style={styles.errorCopy}>
        <Text style={styles.errorText}>{message}</Text>
        {detail ? <Text style={styles.errorDetail}>{detail}</Text> : null}
      </View>
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
  error: { alignItems: 'center', backgroundColor: colors.white, borderColor: '#F1D3D3', borderRadius: radii.inset, borderWidth: 1, flexDirection: 'row', gap: spacing.sm, paddingLeft: spacing.md },
  errorCopy: { flex: 1, gap: 2, paddingVertical: spacing.sm },
  errorDetail: { color: colors.textMuted, fontFamily: fonts.regular, fontSize: 13, lineHeight: 18 },
  errorText: { color: errorText, fontFamily: fonts.regular, fontSize: 15, lineHeight: 21 },
  link: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 15 },
  notice: { alignItems: 'center', backgroundColor: colors.surfaceTint, borderRadius: radii.inset, flexDirection: 'row', gap: spacing.sm, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  noticeText: { color: colors.ink, flex: 1, fontFamily: fonts.regular, fontSize: 14, lineHeight: 20 },
  pressed: { opacity: 0.7 },
  retry: { alignItems: 'center', justifyContent: 'center', minHeight: MIN_TOUCH, paddingHorizontal: spacing.md },
});

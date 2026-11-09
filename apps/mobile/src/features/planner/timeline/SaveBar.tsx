import { Platform, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { Icon, PrimaryButton } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

type Props = {
  disabledReason: string | null;
  onSave: () => void;
};

/**
 * Sticky Save (SCR-024): the one primary action of the proposal. When Save is disabled, a short reason sits above it.
 * Plan Health lives in the cover pill, not here. Bottom padding follows the safe area (this screen has no tab bar).
 */
export function SaveBar({ disabledReason, onSave }: Props) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  return <View style={[s.bar, { paddingBottom: Math.max(insets.bottom, spacing.sm) + spacing.xs }]}>
    <View style={s.inner}>
      {disabledReason ? <View accessibilityLiveRegion="polite" style={s.reason}>
        <Icon color={colors.danger} name="blocked" size={16} strokeWidth={2} />
        <Text numberOfLines={2} style={s.reasonText}>{disabledReason}</Text>
      </View> : null}
      <PrimaryButton
        accessibilityHint={disabledReason ?? t('proposal.save.a11yHint')}
        disabled={!!disabledReason}
        label={t('proposal.save.action')}
        onPress={onSave}
      />
    </View>
  </View>;
}

const s = StyleSheet.create({
  bar: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
    backgroundColor: colors.white,
    ...Platform.select({
      android: { elevation: 12 },
      default: { shadowColor: colors.ink, shadowOffset: { width: 0, height: -4 }, shadowOpacity: 0.06, shadowRadius: 16 },
    }),
  },
  inner: { width: '100%', maxWidth: 480, alignSelf: 'center' },
  reason: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: spacing.xs },
  reasonText: { flex: 1, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: colors.danger },
});

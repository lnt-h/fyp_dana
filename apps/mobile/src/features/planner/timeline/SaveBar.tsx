import { Platform, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { PrimaryButton, SecondaryButton } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { HealthGlyph } from './icons';

type Props = {
  disabledReason: string | null;
  saved: boolean;
  onSave: () => void;
  /** Secondary "Check" action: opens Plan Health (shown when the plan has a server health). */
  onOpenHealth?: () => void;
};

/**
 * Sticky Save (SCR-024): labelled secondary "Check" (Plan Health) beside the primary Save. When Save is disabled, a
 * short reason sits above it. Bottom padding follows the safe area only (this screen has no tab bar).
 */
export function SaveBar({ disabledReason, saved, onSave, onOpenHealth }: Props) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const disabled = saved || !!disabledReason;
  return <View style={[s.bar, { paddingBottom: Math.max(insets.bottom, spacing.sm) + spacing.xs }]}>
    <View style={s.inner}>
      {!!disabledReason && !saved && <View accessibilityLiveRegion="polite" style={s.reason}>
        <HealthGlyph health="BLOCKED" size={16} />
        <Text numberOfLines={2} style={s.reasonText}>{disabledReason}</Text>
      </View>}
      <View style={s.row}>
        {onOpenHealth && <SecondaryButton
          accessibilityHint={t('proposal.save.healthA11y')}
          icon="info"
          label={t('proposal.save.check')}
          onPress={onOpenHealth}
          style={s.secondary}
        />}
        <PrimaryButton
          accessibilityHint={disabledReason ?? t('proposal.save.a11yHint')}
          disabled={disabled}
          icon={saved ? 'check' : undefined}
          label={t(saved ? 'proposal.save.saved' : 'proposal.save.action')}
          onPress={onSave}
          style={s.primary}
        />
      </View>
    </View>
  </View>;
}

const s = StyleSheet.create({
  bar: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
    backgroundColor: colors.white,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.hairline,
    ...Platform.select({
      android: { elevation: 12 },
      default: { shadowColor: colors.ink, shadowOffset: { width: 0, height: -6 }, shadowOpacity: 0.06, shadowRadius: 16 },
    }),
  },
  inner: { width: '100%', maxWidth: 480, alignSelf: 'center' },
  reason: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: spacing.xs },
  reasonText: { flex: 1, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: palette.error },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  secondary: { height: 56, paddingHorizontal: spacing.md },
  primary: { flex: 1, height: 56 },
});

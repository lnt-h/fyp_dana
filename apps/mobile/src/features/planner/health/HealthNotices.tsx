import { StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Icon } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import type { HealthNotice } from './reasons';

/**
 * INFO conflicts from the server (e.g. `LEG_ESTIMATED`) as a neutral "Good to know" group: an info icon in teal, no
 * warning colour, no count in the Plan Health badge. One line per notice type, with the days it applies to.
 */
export function HealthNotices({ notices, dayCount, style }: { notices: HealthNotice[]; dayCount: number; style?: object }) {
  const { t } = useTranslation();
  if (!notices.length) return null;
  return <View style={[n.group, style]}>
    <Text accessibilityRole="header" style={n.title}>{t('proposal.health.notices')}</Text>
    {notices.map(notice => {
      const title = t(`proposal.conflict.${notice.type}`);
      const days = dayCount > 1 && notice.dayIndexes.length
        ? t('proposal.health.noticeDays', { count: notice.dayIndexes.length, days: notice.dayIndexes.join(', ') })
        : null;
      return <View key={notice.type} accessible accessibilityLabel={[t('proposal.health.severityInfo'), title, days].filter(Boolean).join(', ')} style={n.item}>
        <Icon color={colors.tealText} name="info" size={18} />
        <View style={n.copy}>
          <Text style={n.itemTitle}>{title}</Text>
          {days ? <Text style={n.itemBody}>{days}</Text> : null}
        </View>
      </View>;
    })}
  </View>;
}

const n = StyleSheet.create({
  group: { gap: spacing.xs },
  title: { fontFamily: fonts.bold, color: colors.textMuted, fontSize: 11, letterSpacing: 1.6, textTransform: 'uppercase' },
  item: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.xs, padding: spacing.sm, borderRadius: radii.inset, backgroundColor: colors.canvas, borderWidth: 1, borderColor: colors.hairline },
  copy: { flex: 1, minWidth: 0 },
  itemTitle: { fontFamily: fonts.semibold, fontSize: 14, lineHeight: 20, color: colors.ink },
  itemBody: { fontFamily: fonts.regular, fontSize: 13, lineHeight: 18, color: colors.textMuted, marginTop: 2 },
});

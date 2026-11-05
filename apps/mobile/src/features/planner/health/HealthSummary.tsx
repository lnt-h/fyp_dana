import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import type { PlanHealth, Uuid } from '../../../lib/api/types';
import { Icon } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { HealthGlyph } from '../timeline/icons';
import { HealthBadge } from './HealthBadge';
import type { HealthIssue } from './reasons';

/**
 * Plan Health summary (the part of SCR-026 shown inline on the proposal): status line, then the server's reasons
 * grouped Must fix (BLOCKING) / Worth checking (WARNING), each with a shortcut to its stop.
 */
export function HealthSummary({ health, issues, onGoToStop }: { health: PlanHealth; issues: HealthIssue[]; onGoToStop: (dayIndex: number, stopId: Uuid) => void }) {
  const { t } = useTranslation();
  const blocking = issues.filter(issue => issue.severity === 'BLOCKING');
  const warnings = issues.filter(issue => issue.severity !== 'BLOCKING');
  const summary = health === 'GOOD' ? t('proposal.health.summaryGood') : health === 'WARNING' ? t('proposal.health.summaryWarning') : t('proposal.health.summaryBlocked');

  function group(title: string, list: HealthIssue[]) {
    if (!list.length) return null;
    return <View style={h.group}>
      <Text accessibilityRole="header" style={h.groupTitle}>{title}</Text>
      {list.map(issue => <Issue key={issue.key} issue={issue} onGoToStop={onGoToStop} />)}
    </View>;
  }

  return <View style={h.card}>
    <View style={[h.edge, { backgroundColor: edgeColor[health] }]} />
    <View style={h.inner}>
      <View style={h.head}>
        <View style={[h.tile, { backgroundColor: tileColor[health] }]}><HealthGlyph health={health} size={24} /></View>
        <View style={h.headCopy}>
          <Text accessibilityRole="header" style={h.title}>{t('proposal.health.title')}</Text>
          <Text style={[h.status, health === 'BLOCKED' && { color: palette.error }]}>{summary}</Text>
        </View>
      </View>
      {health !== 'GOOD' && <View style={h.badgeRow}><HealthBadge health={health} blocking={blocking.length} warnings={warnings.length} /></View>}
      {health === 'GOOD' && !issues.length && <Text style={h.goodNote}>{t('proposal.health.goodNote')}</Text>}
      {group(t('proposal.health.mustFix'), blocking)}
      {group(t('proposal.health.worthChecking'), warnings)}
      <Text style={h.note}>{t('proposal.health.recheckNote')}</Text>
    </View>
  </View>;
}

function Issue({ issue, onGoToStop }: { issue: HealthIssue; onGoToStop: (dayIndex: number, stopId: Uuid) => void }) {
  const { t } = useTranslation();
  const isBlocking = issue.severity === 'BLOCKING';
  const title = t(`proposal.conflict.${issue.type}`);
  const detail = issue.stopNumber && issue.dayIndex
    ? t('proposal.health.detailStop', { day: issue.dayIndex, name: issue.stopName, number: issue.stopNumber })
    : issue.dayIndex ? t('proposal.health.detailDay', { day: issue.dayIndex }) : null;
  // Server-composed detail (e.g. closing time); shown only when it adds to the title.
  const message = issue.message && issue.message !== title ? issue.message : null;
  const { dayIndex, stopId } = issue;
  return <View style={[h.issue, isBlocking && h.issueBlocking]}>
    <View style={h.issueHead}>
      <HealthGlyph health={isBlocking ? 'BLOCKED' : 'WARNING'} size={16} />
      <Text style={[h.severity, isBlocking && { color: palette.error }]}>{t(isBlocking ? 'proposal.health.severityBlocking' : 'proposal.health.severityWarning')}</Text>
    </View>
    <Text style={h.issueTitle}>{title}</Text>
    {!!message && <Text style={h.issueBody}>{message}</Text>}
    {!!detail && <Text style={h.issueBody}>{detail}</Text>}
    {dayIndex != null && stopId ? <Pressable
      accessibilityRole="button"
      accessibilityLabel={t('proposal.health.goToStopA11y', { name: issue.stopName, number: issue.stopNumber })}
      onPress={() => onGoToStop(dayIndex, stopId)}
      style={({ pressed }) => [h.goTo, pressed && { opacity: 0.6 }]}
    >
      <Text style={h.goToText}>{t('proposal.health.goToStop')}</Text>
      <Icon color={colors.tealText} name="chevron-right" size={16} strokeWidth={2.2} />
    </Pressable> : null}
  </View>;
}

const edgeColor: Record<PlanHealth, string> = { BLOCKED: palette.error, GOOD: colors.audioTeal, WARNING: colors.sun };
const tileColor: Record<PlanHealth, string> = { BLOCKED: '#F8E3E3', GOOD: colors.skyWash, WARNING: '#FDF0DA' };

const h = StyleSheet.create({
  card: { flexDirection: 'row', borderRadius: radii.card, backgroundColor: colors.white, borderWidth: 1, borderColor: '#E4EDF2', overflow: 'hidden' },
  edge: { width: 6 },
  inner: { flex: 1, padding: spacing.md, paddingLeft: spacing.md },
  head: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  tile: { width: 48, height: 48, borderRadius: radii.iconTile, alignItems: 'center', justifyContent: 'center' },
  headCopy: { flex: 1, minWidth: 0 },
  title: { fontFamily: fonts.bold, fontSize: 18, lineHeight: 23, letterSpacing: -0.3, color: colors.ink },
  status: { fontFamily: fonts.bold, fontSize: 14, lineHeight: 19, color: colors.deepOcean, marginTop: 2 },
  badgeRow: { flexDirection: 'row', marginTop: spacing.sm },
  group: { marginTop: spacing.md, gap: 10 },
  groupTitle: { fontFamily: fonts.bold, color: colors.textMuted, fontSize: 11, letterSpacing: 1.6, textTransform: 'uppercase' },
  issue: { borderRadius: 16, backgroundColor: '#F5FAFC', padding: 14, paddingBottom: 4, borderLeftWidth: 4, borderLeftColor: colors.sun },
  issueBlocking: { borderLeftColor: palette.error },
  issueHead: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  severity: { fontFamily: fonts.bold, fontSize: 12, color: colors.deepOcean },
  issueTitle: { fontFamily: fonts.bold, fontSize: 15, lineHeight: 20, color: colors.ink, marginTop: 6 },
  issueBody: { fontFamily: fonts.medium, fontSize: 13, lineHeight: 19, color: colors.textMuted, marginTop: 2 },
  goTo: { flexDirection: 'row', alignItems: 'center', gap: 2, alignSelf: 'flex-start', minHeight: MIN_TOUCH },
  goToText: { fontFamily: fonts.bold, fontSize: 14, color: colors.tealText },
  goodNote: { fontFamily: fonts.medium, fontSize: 14, lineHeight: 20, color: colors.ink, marginTop: spacing.sm },
  note: { fontFamily: fonts.medium, fontSize: 12, lineHeight: 18, color: colors.textMuted, marginTop: spacing.sm },
});

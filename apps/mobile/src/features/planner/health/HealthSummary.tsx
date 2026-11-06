import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import type { PlanHealth, Uuid } from '../../../lib/api/types';
import { Icon } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { currentLocale } from '../../../i18n';
import { formatDate } from '../../place/format';
import { HealthGlyph } from '../timeline/icons';
import { HealthBadge } from './HealthBadge';
import type { HealthIssue } from './reasons';

/**
 * Plan Health summary (the part of SCR-026 shown inline on the proposal): status line, then the server's reasons
 * grouped Must fix (BLOCKING) / Worth checking (WARNING), each with a shortcut to its stop.
 */
export function HealthSummary({ health, issues, onGoToStop, onOpenDetail, updating = false }: {
  health: PlanHealth;
  issues: HealthIssue[];
  onGoToStop: (dayIndex: number, stopId: Uuid) => void;
  /** Opens SCR-026 (full Plan Health detail with fix shortcuts). */
  onOpenDetail?: () => void;
  /** An edit is being recalculated: the previous result stays, greyed (SCR-026 loading). */
  updating?: boolean;
}) {
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

  return <View style={[h.card, updating && h.updating]}>
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
      {onOpenDetail ? <Pressable
        accessibilityRole="button"
        onPress={onOpenDetail}
        style={({ pressed }) => [h.detail, pressed && { opacity: 0.7 }]}
      >
        <Text style={h.detailText}>{t('proposal.healthDetail.openDetail')}</Text>
        <Icon color={colors.white} name="chevron-right" size={18} strokeWidth={2.2} />
      </Pressable> : null}
    </View>
  </View>;
}

/** First sentence of a server reason, for the short summary on the action card. */
function firstSentence(text: string) {
  const match = text.match(/^.*?[.!?](?=\s|$)/);
  return (match ? match[0] : text).trim();
}

/**
 * Plan Health as an action right under the proposal hero. WARNING/BLOCKED: a card with a colour edge, icon + word,
 * the first server reason and a "Review issues" action. GOOD: one quiet line, no card. Status and reasons are the
 * server's (`plan_health`, conflicts); nothing here judges the plan.
 */
export function HealthActionCard({ health, issues, onReview, reviewTargetsStop, updating = false }: {
  health: PlanHealth;
  /** Already sorted by `collectIssues` (blocking first). */
  issues: HealthIssue[];
  /** Scrolls to the first affected stop, or opens SCR-026 when no stop is attached. */
  onReview: () => void;
  reviewTargetsStop: boolean;
  updating?: boolean;
}) {
  const { t } = useTranslation();
  if (health === 'GOOD') {
    return <View accessible accessibilityLabel={t('proposal.healthCard.goodA11y')} style={[h.quiet, updating && h.updating]}>
      <HealthGlyph health="GOOD" size={18} />
      <Text style={h.quietText}>{t('proposal.healthCard.good')}</Text>
    </View>;
  }
  const first = issues[0];
  const reason = first ? firstSentence(first.message || t(`proposal.conflict.${first.type}`)) : null;
  const more = Math.max(0, issues.length - 1);
  const moreText = more > 0 ? t('proposal.healthCard.more', { count: more }) : null;
  const word = t(`proposal.healthCard.${health}`);
  return <View style={[h.card, updating && h.updating]}>
    <View style={[h.edge, { backgroundColor: edgeColor[health] }]} />
    <View style={h.actionInner}>
      <View accessible accessibilityLabel={[word, reason, moreText].filter(Boolean).join('. ')}>
        <View style={h.actionHead}>
          <HealthGlyph health={health} size={20} />
          <Text style={[h.actionWord, health === 'BLOCKED' && { color: palette.error }]}>{word}</Text>
        </View>
        {reason ? <Text numberOfLines={2} style={h.actionReason}>{reason}</Text> : null}
        {moreText ? <Text style={h.actionMore}>{moreText}</Text> : null}
      </View>
      <Pressable
        accessibilityHint={t(reviewTargetsStop ? 'proposal.healthCard.reviewStopHint' : 'proposal.healthCard.reviewDetailHint')}
        accessibilityRole="button"
        onPress={onReview}
        style={({ pressed }) => [h.review, pressed && { opacity: 0.7 }]}
      >
        <Text style={h.reviewText}>{t('proposal.healthCard.review')}</Text>
        <Icon color={colors.deepOcean} name="chevron-right" size={18} strokeWidth={2.2} />
      </Pressable>
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
  const onDate = issue.date ? t('proposal.health.onDate', { date: formatDate(issue.date, currentLocale()) }) : null;
  const affects = issue.affectedStops?.length
    ? t('proposal.health.affects', { stops: issue.affectedStops.map(stop => t('proposal.health.affectedStop', { day: stop.dayIndex, name: stop.name, number: stop.number })).join('; ') })
    : null;
  const { dayIndex, stopId } = issue;
  return <View style={[h.issue, isBlocking && h.issueBlocking]}>
    <View style={h.issueHead}>
      <HealthGlyph health={isBlocking ? 'BLOCKED' : 'WARNING'} size={16} />
      <Text style={[h.severity, isBlocking && { color: palette.error }]}>{t(isBlocking ? 'proposal.health.severityBlocking' : 'proposal.health.severityWarning')}</Text>
    </View>
    <Text style={h.issueTitle}>{title}</Text>
    {!!message && <Text style={h.issueBody}>{message}</Text>}
    {!!onDate && <Text style={h.issueBody}>{onDate}</Text>}
    {!!detail && <Text style={h.issueBody}>{detail}</Text>}
    {!!affects && <Text style={h.issueBody}>{affects}</Text>}
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

const edgeColor: Record<PlanHealth, string> = { BLOCKED: palette.error, GOOD: colors.ok, WARNING: colors.sun };
const tileColor: Record<PlanHealth, string> = { BLOCKED: colors.dangerBg, GOOD: colors.surfaceTint, WARNING: colors.warnBg };

const h = StyleSheet.create({
  card: { flexDirection: 'row', borderRadius: radii.card, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.hairline, overflow: 'hidden' },
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
  issue: { borderRadius: radii.inset, backgroundColor: colors.canvas, padding: 14, paddingBottom: 4, borderLeftWidth: 4, borderLeftColor: colors.sun },
  issueBlocking: { borderLeftColor: palette.error },
  issueHead: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  severity: { fontFamily: fonts.bold, fontSize: 12, color: colors.deepOcean },
  issueTitle: { fontFamily: fonts.bold, fontSize: 15, lineHeight: 20, color: colors.ink, marginTop: 6 },
  issueBody: { fontFamily: fonts.regular, fontSize: 13, lineHeight: 19, color: colors.textMuted, marginTop: 2 },
  goTo: { flexDirection: 'row', alignItems: 'center', gap: 2, alignSelf: 'flex-start', minHeight: MIN_TOUCH },
  goToText: { fontFamily: fonts.bold, fontSize: 14, color: colors.tealText },
  goodNote: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.ink, marginTop: spacing.sm },
  updating: { opacity: 0.55 },
  detail: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 4, minHeight: 48, borderRadius: radii.button, backgroundColor: colors.deepOcean, marginTop: spacing.sm },
  detailText: { fontFamily: fonts.bold, fontSize: 15, color: colors.white },
  actionInner: { flex: 1, gap: 4, paddingVertical: spacing.sm, paddingHorizontal: spacing.md },
  actionHead: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  actionWord: { fontFamily: fonts.bold, fontSize: 16, lineHeight: 22, color: colors.ink },
  actionReason: { fontFamily: fonts.medium, fontSize: 14, lineHeight: 20, color: colors.ink, marginTop: 2 },
  actionMore: { fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: colors.textMuted, marginTop: 2 },
  review: { flexDirection: 'row', alignItems: 'center', gap: 2, alignSelf: 'flex-start', minHeight: MIN_TOUCH, paddingLeft: spacing.md, paddingRight: spacing.sm, marginTop: spacing.xxs, borderRadius: radii.pill, borderWidth: 1.5, borderColor: colors.deepOcean },
  reviewText: { fontFamily: fonts.bold, fontSize: 14, color: colors.deepOcean },
  quiet: { flexDirection: 'row', alignItems: 'center', gap: 6, minHeight: 24 },
  quietText: { fontFamily: fonts.bold, fontSize: 14, lineHeight: 20, color: colors.tealText },
  note: { fontFamily: fonts.medium, fontSize: 12, lineHeight: 18, color: colors.textMuted, marginTop: spacing.sm },
});

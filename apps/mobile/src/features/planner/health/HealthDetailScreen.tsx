/**
 * SCR-026 Plan Health detail (`/plan/[previewId]/health`): the server's reasons grouped Must fix (BLOCKING) / Worth
 * checking (WARNING), then by day and stop, with fix shortcuts that open SCR-027 prefilled on the proposal. The client
 * lists what the server returned; it never derives health, hours or closing times.
 */
import { useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { Chip, CircleButton, Icon, PrimaryButton, Skeleton } from '../../../components/ui';
import type { PlanHealth, Uuid } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { useIsOffline } from '../../home/useNetwork';
import { requestStopIntent, usePendingEdit, type StopIntent } from '../edit/draftStore';
import { InlineBanner, PillButton, editTokens } from '../edit/EditUI';
import { formatTime } from '../timeline/format';
import { HealthGlyph, type PlannerIconName } from '../timeline/icons';
import { useProposal, type ProposalData } from '../timeline/useProposal';
import { collectIssues, countIssues, type HealthIssue } from './reasons';

export function HealthDetailScreen({ previewId }: { previewId: Uuid }) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const { state, reload } = useProposal({ previewId });
  const goBack = () => (router.canGoBack() ? router.back() : router.replace({ params: { previewId }, pathname: '/plan/[previewId]/proposal' }));

  return <View style={[x.screen, { paddingTop: insets.top }]}>
    <StatusBar style="dark" />
    <View style={x.header}>
      <CircleButton accessibilityLabel={t('common.goBack')} icon="back" onPress={goBack} size={44} tone="tint" />
      <Text accessibilityRole="header" numberOfLines={1} style={x.headerTitle}>{t('proposal.healthDetail.title')}</Text>
      <View style={x.headerSpacer} />
    </View>
    {state.status === 'loading'
      ? <View accessibilityLabel={t('proposal.healthDetail.updating')} style={x.pad}>
        <Skeleton height={132} radius={radii.card} />
        <View style={x.gap} />
        <Skeleton height={20} width={120} />
        <View style={x.gap} />
        <Skeleton height={150} radius={radii.card} />
      </View>
      : state.status === 'error' || !state.data.health
        ? <View style={[x.pad, x.center]}>
          <View style={x.errorTile}><Icon color={palette.error} name="warning" size={28} /></View>
          <Text accessibilityRole="alert" style={x.errorTitle}>{t('proposal.healthDetail.error')}</Text>
          <Text style={x.errorBody}>{t('proposal.healthDetail.errorBody')}</Text>
          <PrimaryButton label={t('proposal.error.retry')} onPress={reload} style={x.retry} />
        </View>
        : <HealthDetail data={state.data} health={state.data.health} insetsBottom={insets.bottom} previewId={previewId} />}
  </View>;
}

function HealthDetail({ data, health, previewId, insetsBottom }: { data: ProposalData; health: PlanHealth; previewId: Uuid; insetsBottom: number }) {
  const { t } = useTranslation();
  const offline = useIsOffline();
  const pending = usePendingEdit(previewId);
  const updating = pending?.status === 'applying';
  const [dayFilter, setDayFilter] = useState<number | null>(null);
  const issues = useMemo(() => collectIssues(data.days, data.healthReasons), [data.days, data.healthReasons]);
  const visible = dayFilter == null ? issues : issues.filter(issue => issue.dayIndex === dayFilter || issue.dayIndex == null);
  const { blocking, warnings } = countIssues(visible);
  const shortcutsDisabled = offline || data.readOnly || (!!pending && pending.status !== 'expired');

  const status = health === 'GOOD' ? t('proposal.health.summaryGood') : health === 'WARNING' ? t('proposal.health.summaryWarning') : t('proposal.health.summaryBlocked');
  const counts = [t('proposal.healthDetail.countBlocking', { count: blocking }), t('proposal.healthDetail.countWarnings', { count: warnings })].join(', ');
  const countLine = dayFilter ? `${counts} · ${t('proposal.day.title', { day: dayFilter })}` : counts;
  const dayEnds = [...new Set(data.days.map(day => day.day_window_end).filter((end): end is string => !!end))].join(' / ');

  function openIntent(intent: StopIntent) {
    requestStopIntent(previewId, intent);
    if (router.canGoBack()) router.back();
    else router.replace({ params: { previewId }, pathname: '/plan/[previewId]/proposal' });
  }

  function section(title: string, list: HealthIssue[], severity: 'BLOCKING' | 'WARNING') {
    if (!list.length) return null;
    const byDay = new Map<number | null, HealthIssue[]>();
    list.forEach(issue => byDay.set(issue.dayIndex ?? null, [...(byDay.get(issue.dayIndex ?? null) ?? []), issue]));
    return <View style={x.section}>
      <View style={x.sectionHead}>
        <HealthGlyph health={severity === 'BLOCKING' ? 'BLOCKED' : 'WARNING'} size={18} />
        <Text accessibilityRole="header" style={x.sectionTitle}>{title}</Text>
      </View>
      {[...byDay.entries()].map(([dayIndex, dayIssues]) => <View key={dayIndex ?? 'trip'} style={x.dayGroup}>
        {data.days.length > 1 && dayFilter == null
          ? <Text accessibilityRole="header" style={x.dayLabel}>{dayIndex ? t('proposal.day.title', { day: dayIndex }) : t('proposal.healthDetail.allDays')}</Text>
          : null}
        {dayIssues.map(issue => <IssueCard key={issue.key} data={data} disabled={shortcutsDisabled} issue={issue} onIntent={openIntent} />)}
      </View>)}
    </View>;
  }

  return <ScrollView contentContainerStyle={[x.pad, { paddingBottom: insetsBottom + spacing.xxl }]} showsVerticalScrollIndicator={false}>
    <View style={[x.summary, updating && x.dim]}>
      <View style={[x.edge, { backgroundColor: edgeColor[health] }]} />
      <View style={x.summaryInner}>
        <View style={[x.tile, { backgroundColor: tileColor[health] }]}><HealthGlyph health={health} size={30} /></View>
        <Text style={[x.status, health === 'BLOCKED' && { color: palette.error }]}>{status}</Text>
        {health !== 'GOOD' || issues.length ? <Text style={x.counts}>{countLine}</Text> : null}
      </View>
    </View>

    {updating ? <InlineBanner style={x.banner} title={t('proposal.healthDetail.updating')} tone="progress" /> : null}
    {offline ? <InlineBanner style={x.banner} title={t('proposal.healthDetail.offline')} tone="warning" /> : null}

    {data.days.length > 1 && issues.length ? <View accessibilityLabel={t('proposal.healthDetail.filterA11y')} accessibilityRole="tablist" style={x.filters}>
      <Chip label={t('proposal.healthDetail.allDays')} onPress={() => setDayFilter(null)} selected={dayFilter === null} />
      {data.days.map(day => <Chip key={day.day_index} label={t('proposal.day.title', { day: day.day_index })} onPress={() => setDayFilter(day.day_index)} selected={dayFilter === day.day_index} />)}
    </View> : null}

    <View style={updating ? x.dim : undefined}>
      {section(t('proposal.health.mustFix'), visible.filter(issue => issue.severity === 'BLOCKING'), 'BLOCKING')}
      {section(t('proposal.health.worthChecking'), visible.filter(issue => issue.severity !== 'BLOCKING'), 'WARNING')}
      {!visible.length ? <View style={x.good}>
        <Icon color={colors.tealText} name="check" size={22} />
        <Text style={x.goodText}>{dayFilter ? t('proposal.healthDetail.noIssues') : dayEnds ? t('proposal.healthDetail.goodBody', { end: dayEnds }) : t('proposal.health.goodNote')}</Text>
      </View> : null}
    </View>
    <Text style={x.note}>{t('proposal.health.recheckNote')}</Text>
  </ScrollView>;
}

type Fix = { label: string; icon: PlannerIconName; run: () => void };

function IssueCard({ issue, data, disabled, onIntent }: { issue: HealthIssue; data: ProposalData; disabled: boolean; onIntent: (intent: StopIntent) => void }) {
  const { t } = useTranslation();
  const isBlocking = issue.severity === 'BLOCKING';
  const title = t(`proposal.conflict.${issue.type}`);
  const message = issue.message && issue.message !== title ? issue.message : null;
  const arrival = formatTime(issue.arrival);
  const departure = formatTime(issue.departure);
  const where = issue.dayIndex && issue.stopNumber
    ? t('proposal.health.detailStop', { day: issue.dayIndex, name: issue.stopName, number: issue.stopNumber })
    : issue.dayIndex ? t('proposal.health.detailDay', { day: issue.dayIndex }) : null;
  const legTo = issue.source === 'leg' && issue.toStopNumber ? t('proposal.healthDetail.legTo', { name: issue.toStopName, number: issue.toStopNumber }) : null;
  const day = data.days.find(item => item.day_index === issue.dayIndex);
  const lastStop = day?.stops[day.stops.length - 1];

  const fixes: Fix[] = [];
  switch (issue.type) {
    case 'CLOSED_AT_PLANNED_TIME':
      if (issue.stopId) { const stopId = issue.stopId; fixes.push({ icon: 'toStart', label: t('proposal.healthDetail.fixMove'), run: () => onIntent({ focus: 'move', kind: 'edit', moveToStart: true, stopId }) }); }
      break;
    case 'LEG_UNAVAILABLE':
      if (issue.toStopId) {
        const stopId = issue.toStopId;
        fixes.push({ icon: 'drive', label: t('proposal.healthDetail.fixMode'), run: () => onIntent({ focus: 'mode', kind: 'edit', stopId }) });
        fixes.push({ icon: 'swap', label: t('proposal.healthDetail.fixReplace'), run: () => onIntent({ focus: 'replace', kind: 'edit', stopId }) });
      }
      break;
    case 'DAY_WINDOW_EXCEEDED': {
      const stopId = issue.stopId ?? lastStop?.id;
      if (stopId) fixes.push({ icon: 'minus', label: t('proposal.healthDetail.fixShorten'), run: () => onIntent({ focus: 'duration', kind: 'edit', stopId }) });
      break;
    }
    case 'OPENING_HOURS_UNKNOWN':
    case 'FACT_STALE':
      if (issue.placeId) { const placeId = issue.placeId; fixes.push({ icon: 'card', label: t('proposal.healthDetail.fixPlaceCard'), run: () => router.push({ params: { placeId }, pathname: '/place/[placeId]' }) }); }
      break;
    default:
      break;
  }
  const goTo = issue.dayIndex != null && issue.stopId ? { dayIndex: issue.dayIndex, stopId: issue.stopId } : null;
  const name = issue.toStopName ?? issue.stopName ?? '';

  return <View accessibilityLabel={[t(isBlocking ? 'proposal.health.severityBlocking' : 'proposal.health.severityWarning'), title, where].filter(Boolean).join(', ')} style={[x.issue, isBlocking && x.issueBlocking]}>
    <View style={[x.badge, isBlocking ? x.badgeBlocking : x.badgeWarning]}>
      <HealthGlyph health={isBlocking ? 'BLOCKED' : 'WARNING'} size={14} />
      <Text style={[x.badgeText, isBlocking ? { color: palette.error } : { color: editTokens.warnText }]}>{t(isBlocking ? 'proposal.health.severityBlocking' : 'proposal.health.severityWarning')}</Text>
    </View>
    <Text style={x.issueTitle}>{title}</Text>
    {where ? <Text style={x.issueWhere}>{where}</Text> : null}
    {legTo ? <Text style={x.issueBody}>{legTo}</Text> : null}
    {arrival && departure && issue.source === 'stop' ? <Text style={x.issueBody}>{t('proposal.healthDetail.arriveLeave', { arrival, departure })}</Text> : null}
    {message ? <Text style={x.issueBody}>{message}</Text> : null}
    {fixes.length || goTo ? <View style={x.actions}>
      {fixes.map((fix, index) => <PillButton
        key={fix.label}
        accessibilityLabel={t('proposal.healthDetail.fixA11y', { action: fix.label, name })}
        disabled={disabled && fix.icon !== 'card'}
        icon={fix.icon}
        label={fix.label}
        onPress={fix.run}
        tone={index === 0 ? 'primary' : 'default'}
      />)}
      {goTo ? <PillButton
        accessibilityLabel={t('proposal.health.goToStopA11y', { name: issue.stopName, number: issue.stopNumber })}
        label={t('proposal.health.goToStop')}
        onPress={() => onIntent({ dayIndex: goTo.dayIndex, kind: 'goto', stopId: goTo.stopId })}
      /> : null}
    </View> : null}
  </View>;
}

const edgeColor: Record<PlanHealth, string> = { BLOCKED: palette.error, GOOD: colors.audioTeal, WARNING: colors.sun };
const tileColor: Record<PlanHealth, string> = { BLOCKED: colors.dangerBg, GOOD: colors.surfaceTint, WARNING: colors.warnBg };

const x = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.canvas },
  header: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingHorizontal: spacing.md, paddingVertical: spacing.xs },
  headerTitle: { ...typography.headline, flex: 1, textAlign: 'center' },
  headerSpacer: { width: 44 },
  pad: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm, width: '100%', maxWidth: 560, alignSelf: 'center' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  gap: { height: spacing.md },
  errorTile: { width: 64, height: 64, borderRadius: 32, backgroundColor: editTokens.errorBg, alignItems: 'center', justifyContent: 'center' },
  errorTitle: { ...typography.headline, textAlign: 'center', marginTop: spacing.md },
  errorBody: { ...typography.body, color: colors.textMuted, textAlign: 'center', marginTop: spacing.xxs },
  retry: { alignSelf: 'stretch', marginTop: spacing.xl },
  summary: { flexDirection: 'row', borderRadius: radii.card, borderWidth: 1, borderColor: editTokens.cardBorder, overflow: 'hidden', backgroundColor: colors.white },
  edge: { width: 6 },
  summaryInner: { flex: 1, alignItems: 'center', padding: spacing.lg },
  tile: { width: 60, height: 60, borderRadius: 30, alignItems: 'center', justifyContent: 'center' },
  status: { ...typography.headline, textAlign: 'center', marginTop: spacing.sm },
  counts: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textMuted, textAlign: 'center', marginTop: 2 },
  dim: { opacity: 0.5 },
  banner: { marginTop: spacing.sm },
  filters: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.md },
  section: { marginTop: spacing.xl },
  sectionHead: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: spacing.xs },
  sectionTitle: { fontFamily: fonts.bold, fontSize: 18, lineHeight: 23, letterSpacing: -0.3, color: colors.ink },
  dayGroup: { gap: spacing.xs, marginTop: spacing.xs },
  dayLabel: { fontFamily: fonts.bold, fontSize: 11, letterSpacing: 1.4, textTransform: 'uppercase', color: colors.textMuted, marginTop: spacing.xs },
  issue: { borderRadius: radii.card, borderWidth: 1, borderColor: editTokens.cardBorder, borderLeftWidth: 5, borderLeftColor: colors.sun, backgroundColor: colors.white, padding: spacing.md },
  issueBlocking: { borderLeftColor: palette.error },
  badge: { flexDirection: 'row', alignItems: 'center', gap: 5, alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 4, borderRadius: radii.chip },
  badgeBlocking: { backgroundColor: editTokens.errorBg },
  badgeWarning: { backgroundColor: editTokens.warnBg },
  badgeText: { fontFamily: fonts.bold, fontSize: 12 },
  issueTitle: { fontFamily: fonts.bold, fontSize: 16, lineHeight: 22, color: colors.ink, marginTop: spacing.xs },
  issueWhere: { fontFamily: fonts.bold, fontSize: 14, lineHeight: 20, color: colors.deepOcean, marginTop: 2 },
  issueBody: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textMuted, marginTop: 2 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.sm },
  good: { flexDirection: 'row', gap: spacing.xs, alignItems: 'flex-start', marginTop: spacing.lg, padding: spacing.md, borderRadius: radii.card, backgroundColor: colors.surfaceTint },
  goodText: { flex: 1, fontFamily: fonts.regular, fontSize: 15, lineHeight: 22, color: colors.ink },
  note: { fontFamily: fonts.regular, fontSize: 13, lineHeight: 19, color: colors.textMuted, marginTop: spacing.lg },
});

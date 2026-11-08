/**
 * SCR-026 Plan Health detail (`/plan/[previewId]/health`): the server's status as the same pill as the proposal, then
 * the real problems first (BLOCKING, then WARNING) as compact rows with fix shortcuts that open SCR-027 on the proposal,
 * then ONE quiet note for stops whose hours are not listed (DEC-030). Titles are always localized from the conflict
 * type; the server's English `message` is never shown. The client never derives health, hours or closing times.
 */
import { useEffect, useMemo, useRef } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { CircleButton, Icon, PrimaryButton, Skeleton, type IconName } from '../../../components/ui';
import type { PlanHealth, Uuid } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { useIsOffline } from '../../home/useNetwork';
import { requestStopIntent, usePendingEdit, type StopIntent } from '../edit/draftStore';
import { InlineBanner } from '../edit/EditUI';
import { currentLocale } from '../../../i18n';
import { formatDate } from '../../place/format';
import { useProposal, type ProposalData } from '../timeline/useProposal';
import { HealthPill } from './HealthPill';
import { collectIssues, unknownHoursStopCount, type HealthIssue } from './reasons';

export function HealthDetailScreen({ previewId }: { previewId: Uuid }) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const { state, reload, refresh } = useProposal({ previewId });
  const goBack = () => (router.canGoBack() ? router.back() : router.replace({ params: { previewId }, pathname: '/plan/[previewId]/proposal' }));

  // An edit that was still recalculating when this screen opened: show its revision once it lands (no stale health).
  const pending = usePendingEdit(previewId);
  const hadPending = useRef(!!pending);
  useEffect(() => {
    if (pending) { hadPending.current = true; return; }
    if (hadPending.current) { hadPending.current = false; void refresh(); }
  }, [pending, refresh]);

  return <View style={[x.screen, { paddingTop: insets.top }]}>
    <StatusBar style="dark" />
    <View style={x.header}>
      <CircleButton accessibilityLabel={t('common.goBack')} icon="back" onPress={goBack} size={44} tone="tint" />
      <Text accessibilityRole="header" numberOfLines={1} style={x.headerTitle}>{t('proposal.healthDetail.title')}</Text>
      <View style={x.headerSpacer} />
    </View>
    {state.status === 'loading'
      ? <View accessibilityLabel={t('proposal.healthDetail.updating')} style={x.pad}>
        <Skeleton height={32} radius={radii.pill} width={140} />
        <View style={x.gap} />
        {[0, 1, 2].map(key => <View key={key} style={x.skeletonRow}><Skeleton height={40} radius={radii.iconTile} width={40} /><View style={x.flex}><Skeleton height={16} width="70%" /><View style={x.gapSm} /><Skeleton height={14} width="45%" /></View></View>)}
      </View>
      : state.status === 'error' || !state.data.health
        ? <View style={[x.pad, x.center]}>
          <View style={x.errorTile}><Icon color={colors.danger} name="warning" size={28} /></View>
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
  const issues = useMemo(() => collectIssues(data.days, data.healthReasons), [data.days, data.healthReasons]);
  const unknownHours = useMemo(() => unknownHoursStopCount(data.days, data.healthReasons), [data.days, data.healthReasons]);
  const shortcutsDisabled = offline || data.readOnly || (!!pending && pending.status !== 'expired');
  const blocking = issues.filter(issue => issue.severity === 'BLOCKING');
  const warnings = issues.filter(issue => issue.severity !== 'BLOCKING');
  const summary = health === 'BLOCKED' ? t('proposal.healthDetail.summaryBlocked')
    : issues.length ? t('proposal.healthDetail.summaryWarning') : t('proposal.healthDetail.summaryGood');

  function openIntent(intent: StopIntent) {
    requestStopIntent(previewId, intent);
    if (router.canGoBack()) router.back();
    else router.replace({ params: { previewId }, pathname: '/plan/[previewId]/proposal' });
  }

  function section(title: string, list: HealthIssue[]) {
    if (!list.length) return null;
    return <View style={x.section}>
      <Text accessibilityRole="header" style={x.sectionTitle}>{title}</Text>
      <View style={x.rows}>
        {list.map(issue => <IssueRow key={issue.key} data={data} disabled={shortcutsDisabled} issue={issue} onIntent={openIntent} />)}
      </View>
    </View>;
  }

  return <ScrollView contentContainerStyle={[x.pad, { paddingBottom: insetsBottom + spacing.xxl }]} showsVerticalScrollIndicator={false}>
    <View style={[x.summary, updating && x.dim]}>
      <HealthPill health={health} problems={issues.length} updating={updating} />
      <Text style={x.summaryText}>{summary}</Text>
    </View>

    {offline ? <InlineBanner style={x.banner} title={t('proposal.healthDetail.offline')} tone="warning" /> : null}

    <View style={updating ? x.dim : undefined}>
      {section(t('proposal.health.mustFix'), blocking)}
      {section(t('proposal.health.worthChecking'), warnings)}
      {!issues.length ? <View style={x.good}>
        <View style={[x.tile, { backgroundColor: colors.successBg }]}><Icon color={colors.success} name="check" size={20} strokeWidth={2.2} /></View>
        <Text style={x.goodText}>{t('proposal.healthDetail.noProblems')}</Text>
      </View> : null}
      {unknownHours > 0 ? <View accessible style={x.quiet}>
        <Icon color={colors.textMuted} name="clock" size={16} />
        <Text style={x.quietText}>{t('proposal.healthDetail.hoursNotListed', { count: unknownHours })}</Text>
      </View> : null}
    </View>
    <Text style={x.note}>{t('proposal.health.recheckNote')}</Text>
  </ScrollView>;
}

type Fix = { label: string; run: () => void; needsEdit: boolean };

function IssueRow({ issue, data, disabled, onIntent }: { issue: HealthIssue; data: ProposalData; disabled: boolean; onIntent: (intent: StopIntent) => void }) {
  const { t } = useTranslation();
  const isBlocking = issue.severity === 'BLOCKING';
  const title = t(`proposal.conflict.${issue.type}`);
  const name = issue.toStopName ?? issue.stopName ?? '';
  const where = issue.dayIndex && issue.stopNumber
    ? t('proposal.health.detailStop', { day: issue.dayIndex, name: issue.stopName, number: issue.stopNumber })
    : issue.dayIndex ? t('proposal.health.detailDay', { day: issue.dayIndex }) : null;
  const legTo = issue.source === 'leg' && issue.toStopNumber ? t('proposal.healthDetail.legTo', { name: issue.toStopName, number: issue.toStopNumber }) : null;
  const onDate = issue.date ? t('proposal.health.onDate', { date: formatDate(issue.date, currentLocale()) }) : null;
  // Stops already named in the row (the stop, or both ends of a leg) are not repeated under "Affects".
  const others = issue.affectedStops?.filter(stop => stop.id !== issue.stopId && stop.id !== issue.toStopId) ?? [];
  const affects = others.length
    ? t('proposal.health.affects', { stops: others.map(stop => t('proposal.health.affectedStop', { day: stop.dayIndex, name: stop.name, number: stop.number })).join('; ') })
    : null;
  const detail = [where, legTo, onDate].filter(Boolean).join(' · ');
  const day = data.days.find(item => item.day_index === issue.dayIndex);
  const lastStop = day?.stops[day.stops.length - 1];

  const fixes: Fix[] = [];
  const edit = (label: string, intent: StopIntent) => fixes.push({ label, needsEdit: true, run: () => onIntent(intent) });
  switch (issue.type) {
    case 'CLOSED_AT_PLANNED_TIME':
      if (issue.stopId) edit(t('proposal.healthDetail.fixMove'), { focus: 'move', kind: 'edit', moveToStart: true, stopId: issue.stopId });
      break;
    case 'LEG_UNAVAILABLE':
      if (issue.toStopId) {
        edit(t('proposal.healthDetail.fixMode'), { focus: 'mode', kind: 'edit', stopId: issue.toStopId });
        edit(t('proposal.healthDetail.fixReplace'), { focus: 'replace', kind: 'edit', stopId: issue.toStopId });
      }
      break;
    case 'DAY_WINDOW_EXCEEDED': {
      const stopId = issue.stopId ?? lastStop?.id;
      if (stopId) edit(t('proposal.healthDetail.fixShorten'), { focus: 'duration', kind: 'edit', stopId });
      break;
    }
    case 'LEG_MODE_RESTRICTED':
      if (issue.toStopId) edit(t('proposal.healthDetail.fixMode'), { focus: 'mode', kind: 'edit', stopId: issue.toStopId });
      break;
    case 'CLOSED_ON_DATE':
    case 'LUNAR_EVENT_CONFLICT':
    case 'WEB_PLACE_UNVERIFIED':
    case 'WEB_PLACE_UNRESOLVED':
      if (issue.stopId) edit(t('proposal.healthDetail.fixReplace'), { focus: 'replace', kind: 'edit', stopId: issue.stopId });
      break;
    case 'FACT_STALE':
    case 'TICKET_VALIDITY':
    case 'SEASONAL_WARNING':
      if (issue.placeId) { const placeId = issue.placeId; fixes.push({ label: t('proposal.healthDetail.fixPlaceCard'), needsEdit: false, run: () => router.push({ params: { placeId }, pathname: '/place/[placeId]' }) }); }
      break;
    default:
      break;
  }
  const goTo = issue.dayIndex != null && issue.stopId ? { dayIndex: issue.dayIndex, stopId: issue.stopId } : null;
  const icon: IconName = isBlocking ? 'blocked' : 'warning';
  const severity = t(isBlocking ? 'proposal.health.severityBlocking' : 'proposal.health.severityWarning');

  return <View style={x.row}>
    <View accessible accessibilityLabel={[severity, title, detail, affects].filter(Boolean).join(', ')} style={x.rowMain}>
      <View style={[x.tile, { backgroundColor: isBlocking ? colors.dangerBg : colors.warningBg }]}>
        <Icon color={isBlocking ? colors.danger : colors.warning} name={icon} size={20} strokeWidth={2} />
      </View>
      <View style={x.flex}>
        <Text style={x.rowTitle}>{title}</Text>
        {detail ? <Text style={x.rowDetail}>{detail}</Text> : null}
        {affects ? <Text style={x.rowDetail}>{affects}</Text> : null}
      </View>
    </View>
    {fixes.length || goTo ? <View style={x.actions}>
      {fixes.map(fix => <TextAction key={fix.label} accessibilityLabel={t('proposal.healthDetail.fixA11y', { action: fix.label, name })} disabled={disabled && fix.needsEdit} label={fix.label} onPress={fix.run} />)}
      {goTo ? <TextAction
        accessibilityLabel={t('proposal.health.goToStopA11y', { name: issue.stopName, number: issue.stopNumber })}
        label={t('proposal.health.goToStop')}
        onPress={() => onIntent({ dayIndex: goTo.dayIndex, kind: 'goto', stopId: goTo.stopId })}
      /> : null}
    </View> : null}
  </View>;
}

function TextAction({ label, onPress, disabled, accessibilityLabel }: { label: string; onPress: () => void; disabled?: boolean; accessibilityLabel?: string }) {
  return <Pressable
    accessibilityLabel={accessibilityLabel ?? label}
    accessibilityRole="button"
    accessibilityState={{ disabled: !!disabled }}
    disabled={disabled}
    hitSlop={4}
    onPress={onPress}
    style={({ pressed }) => [x.action, disabled && x.dim, pressed && x.pressed]}
  >
    <Text style={x.actionText}>{label}</Text>
  </Pressable>;
}

const TILE = 40;

const x = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.canvas },
  header: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingHorizontal: spacing.md, paddingVertical: spacing.xs },
  headerTitle: { ...typography.headline, flex: 1, textAlign: 'center' },
  headerSpacer: { width: 44 },
  pad: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm, width: '100%', maxWidth: 560, alignSelf: 'center' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  flex: { flex: 1, minWidth: 0 },
  gap: { height: spacing.lg },
  gapSm: { height: spacing.xs },
  skeletonRow: { flexDirection: 'row', gap: spacing.sm, alignItems: 'center', marginBottom: spacing.md },
  errorTile: { width: 64, height: 64, borderRadius: 32, backgroundColor: colors.dangerBg, alignItems: 'center', justifyContent: 'center' },
  errorTitle: { ...typography.headline, textAlign: 'center', marginTop: spacing.md },
  errorBody: { ...typography.body, color: colors.textMuted, textAlign: 'center', marginTop: spacing.xxs },
  retry: { alignSelf: 'stretch', marginTop: spacing.xl },
  summary: { gap: spacing.xs },
  summaryText: { ...typography.body, color: colors.textSecondary },
  dim: { opacity: 0.5 },
  pressed: { opacity: 0.6 },
  banner: { marginTop: spacing.md },
  section: { marginTop: spacing.xl },
  sectionTitle: { ...typography.headline, marginBottom: spacing.xs },
  rows: { borderRadius: radii.card, backgroundColor: colors.surface, paddingHorizontal: spacing.md },
  row: { paddingVertical: spacing.sm, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.hairline },
  rowMain: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm },
  tile: { width: TILE, height: TILE, borderRadius: radii.iconTile, alignItems: 'center', justifyContent: 'center' },
  rowTitle: { ...typography.bodyStrong },
  rowDetail: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textSecondary, marginTop: 1 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', columnGap: spacing.md, paddingLeft: TILE + spacing.sm },
  action: { minHeight: MIN_TOUCH, justifyContent: 'center' },
  actionText: { fontFamily: fonts.semibold, fontSize: 15, color: colors.primary },
  good: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.xl, padding: spacing.md, borderRadius: radii.card, backgroundColor: colors.surface },
  goodText: { ...typography.body, flex: 1 },
  quiet: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.xs, marginTop: spacing.lg },
  quietText: { flex: 1, fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textMuted },
  note: { fontFamily: fonts.regular, fontSize: 13, lineHeight: 19, color: colors.textMuted, marginTop: spacing.md },
});

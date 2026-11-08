/**
 * SCR-024 Proposal timeline + SCR-025 Proposal map, one screen showing the same revision (FR-088): a selection made on
 * the map or in the timeline is the same selection. Nothing here computes times, legs or Plan Health.
 *
 * Params: `previewId`; optional `tripId` and `mode=saved|draft` (from My trips). `mode=saved` shows the saved itinerary
 * read-only. Editing (SCR-027/028/030) sends op lists to the server and renders the revision it returns; pending edits
 * live in the draft store until acknowledged (ADR-009).
 */
import { useCallback, useEffect, useMemo, useRef, useState, type ComponentRef } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { CircleButton, Icon, PrimaryButton, SectionHeader, Skeleton } from '../../../components/ui';
import { takeStopIntent } from '../../../features/planner/edit/draftStore';
import { EditStatusBanner } from '../../../features/planner/edit/EditStatusBanner';
import { EditStopSheet, type EditTarget } from '../../../features/planner/edit/EditStopSheet';
import { PillButton } from '../../../features/planner/edit/EditUI';
import { regenerationEnabled } from '../../../features/planner/edit/flags';
import { RegenerateDaySheet } from '../../../features/planner/edit/RegenerateDaySheet';
import { usePreviewEditor } from '../../../features/planner/edit/usePreviewEditor';
import { HealthActionCard, HealthSummary } from '../../../features/planner/health/HealthSummary';
import { PlacePicker, type PickerMode } from '../../../features/planner/picker/PlacePicker';
import { useIsOffline } from '../../../features/home/useNetwork';
import { collectIssues } from '../../../features/planner/health/reasons';
import { ProposalMap } from '../../../features/planner/map/ProposalMap';
import { DayCard } from '../../../features/planner/timeline/DayCard';
import { DayTabs } from '../../../features/planner/timeline/DayTabs';
import { HERO_RADIUS, ProposalHeader, proposalHeroHeight } from '../../../features/planner/timeline/ProposalHeader';
import { SaveBar } from '../../../features/planner/timeline/SaveBar';
import { dayDate, formatShortDate } from '../../../features/planner/timeline/format';
import { PlannerIcon } from '../../../features/planner/timeline/icons';
import { useProposal, type ProposalData } from '../../../features/planner/timeline/useProposal';
import { useReducedMotion } from '../../../hooks/useReducedMotion';
import { SaveSheet, webUnverifiedStopNames } from '../../../features/save';
import { HandoffSheet } from '../../../features/handoff';
import { currentLocale } from '../../../i18n';
import { MAX_STOPS_PER_DAY, type PreviewEditOperation } from '../../../lib/api/sourcePlanning';
import type { PlanPreview, Uuid } from '../../../lib/api/types';
import { CITY_IMAGES } from '../../../lib/images/cityImages';
import { colors } from '../../../theme/colors';
import { elevation } from '../../../theme/elevation';
import { radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';

type ViewElement = ComponentRef<typeof View>;

export default function ProposalScreen() {
  const params = useLocalSearchParams<{ previewId: string; tripId?: string; mode?: string }>();
  const mode = params.mode === 'saved' || params.mode === 'draft' ? params.mode : undefined;
  const { state, reload, applyPreview } = useProposal({ mode, previewId: params.previewId, tripId: params.tripId });
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();

  const goBack = () => (router.canGoBack() ? router.back() : router.replace('/home'));

  if (state.status === 'loading') {
    return <View accessibilityLabel={t('proposal.loading')} accessibilityLiveRegion="polite" style={st.screen}>
      <StatusBar style="light" />
      <View style={st.skeletonHero}><Skeleton height={proposalHeroHeight(insets.top)} radius={0} /></View>
      <View style={[st.floatingBack, { top: insets.top + spacing.xs }]}>
        <CircleButton accessibilityLabel={t('common.goBack')} icon="back" onPress={goBack} size={44} />
      </View>
      <View style={st.skeletonMeta}><Skeleton height={18} width={160} /></View>
      <View style={st.skeletonBody}>
        <Skeleton height={96} radius={radii.card} />
        <Skeleton height={24} width={120} />
        <Skeleton height={220} radius={radii.card} />
        <Skeleton height={88} radius={radii.card} />
      </View>
    </View>;
  }

  if (state.status === 'error') {
    const notFound = state.code === 'resource_not_found';
    return <View style={[st.screen, st.center, { paddingTop: insets.top }]}>
      <StatusBar style="dark" />
      <View style={[st.floatingBack, { top: insets.top + spacing.xs }]}>
        <CircleButton accessibilityLabel={t('common.goBack')} icon="back" onPress={goBack} size={44} tone="tint" />
      </View>
      <View style={st.errorTile}><Icon color={colors.tealText} name={notFound ? 'map-pin' : 'warning'} size={30} /></View>
      <Text accessibilityLiveRegion="assertive" accessibilityRole="alert" style={st.errorTitle}>{t(notFound ? 'proposal.error.notFound' : 'proposal.error.generic')}</Text>
      <Text style={st.errorBody}>{t(notFound ? 'proposal.error.notFoundBody' : 'proposal.error.genericBody')}</Text>
      {!notFound && <PrimaryButton label={t('proposal.error.retry')} onPress={reload} style={st.retry} />}
    </View>;
  }

  return <Proposal data={state.data} goBack={goBack} onPreview={applyPreview} previewId={params.previewId} />;
}

type Toast = { text: string; tone: 'success' | 'info' };

function Proposal({ data, goBack, onPreview, previewId: routePreviewId }: { data: ProposalData; goBack: () => void; onPreview: (preview: PlanPreview) => Promise<void>; previewId: Uuid }) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const reducedMotion = useReducedMotion();
  const scrollRef = useRef<ComponentRef<typeof ScrollView>>(null);
  const contentRef = useRef<ViewElement>(null);
  const healthRef = useRef<ViewElement>(null);
  const rowRefs = useRef<Record<Uuid, ViewElement | null>>({});
  const { days } = data;

  const [activeDay, setActiveDay] = useState<number>(days[0]?.day_index ?? 1);
  const [openDay, setOpenDay] = useState<number | null>(days[0]?.day_index ?? null);
  // Selection is kept per day (SCR-024 "selection kept per day"); defaults to the day's first stop.
  const [selection, setSelection] = useState<Record<number, Uuid>>(() =>
    Object.fromEntries(days.filter(day => day.stops[0]).map(day => [day.day_index, day.stops[0].id])));
  const [saved, setSaved] = useState(data.saved);
  const [toast, setToast] = useState<Toast | null>(null);
  const [saveOpen, setSaveOpen] = useState(false);
  const [handoffOpen, setHandoffOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null);
  const [picker, setPicker] = useState<PickerMode | null>(null);
  const [regenDay, setRegenDay] = useState<number | null>(null);
  const [regenerating, setRegenerating] = useState(false);
  const offline = useIsOffline();

  const previewId = data.previewId ?? routePreviewId;
  const editable = !data.readOnly && data.previewId != null && data.previewRevision != null;
  const editor = usePreviewEditor({ onPreview, previewId, revision: data.previewRevision });
  const { pending } = editor;
  const recalculating = regenerating || pending?.status === 'applying';
  const editDisabled = offline || !!pending || regenerating;

  // A new revision may remove the selected stop: fall back to the day's first stop.
  useEffect(() => {
    setSelection(current => {
      const next: Record<number, Uuid> = {};
      days.forEach(day => {
        const kept = current[day.day_index];
        const id = kept && day.stops.some(stop => stop.id === kept) ? kept : day.stops[0]?.id;
        if (id) next[day.day_index] = id;
      });
      return next;
    });
  }, [days]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 4000);
    return () => clearTimeout(timer);
  }, [toast]);

  const day = days.find(item => item.day_index === activeDay) ?? days[0];
  const issues = useMemo(() => collectIssues(days, data.healthReasons), [days, data.healthReasons]);
  const stopCount = days.reduce((sum, item) => sum + item.stops.length, 0);
  const city = data.cityName ?? t('proposal.tripFallback');
  const firstStop = days.find(item => item.stops.length)?.stops[0];
  const cityImage = data.cityCode ? CITY_IMAGES[data.cityCode] : null;
  const heroImage = data.cover ?? cityImage;
  const heroLabel = data.cover
    ? data.cover.alt_text ?? t('proposal.cover.photo', { name: firstStop?.name ?? '' })
    : t('proposal.cover.cityPhoto', { city });

  function dateOf(dayIndex: number) {
    return data.startDate ? formatShortDate(dayDate(data.startDate, dayIndex), currentLocale()) : '';
  }

  function scrollToView(view: ViewElement | null | undefined, offset = 96) {
    const content = contentRef.current;
    if (!view || !content) return;
    view.measureLayout(content, (_x: number, y: number) => {
      scrollRef.current?.scrollTo({ animated: !reducedMotion, y: Math.max(0, y - offset) });
    }, () => undefined);
  }

  function select(dayIndex: number, stopId: Uuid) {
    setSelection(current => ({ ...current, [dayIndex]: stopId }));
  }

  function showDay(dayIndex: number) {
    setActiveDay(dayIndex);
    setOpenDay(dayIndex);
  }

  function toggleDay(dayIndex: number) {
    if (openDay === dayIndex) { setOpenDay(null); return; }
    showDay(dayIndex);
  }

  function goToStop(dayIndex: number, stopId: Uuid) {
    showDay(dayIndex);
    select(dayIndex, stopId);
    // Wait for the day's card to expand and lay out before scrolling to the stop.
    setTimeout(() => scrollToView(rowRefs.current[stopId]), 80);
  }

  const emptyDay = days.find(item => item.stops.length === 0);
  const disabledReason = offline
    ? t('proposal.edit.saveOffline')
    : recalculating
      ? t('proposal.edit.saveWhileRecalculating')
      : pending
        ? t('proposal.edit.saveWhilePending')
        : data.health === 'BLOCKED'
          ? t('proposal.save.blockedShort')
          : emptyDay ? t('proposal.save.emptyDayShort', { day: emptyDay.day_index }) : null;

  function save() {
    // SCR-029: explicit Save through the confirm sheet (API-022, Idempotency-Key, expected revisions).
    setSaveOpen(true);
  }


  const openHealth = data.health
    ? () => (data.previewId ? router.push({ params: { previewId: data.previewId }, pathname: '/plan/[previewId]/health' }) : scrollToView(healthRef.current, 24))
    : undefined;

  // "Review issues" on the Health card: the first affected stop (issues are sorted blocking first), else SCR-026.
  const firstStopIssue = issues.find(issue => issue.dayIndex != null && issue.stopId);
  function reviewIssues() {
    if (firstStopIssue?.dayIndex != null && firstStopIssue.stopId) goToStop(firstStopIssue.dayIndex, firstStopIssue.stopId);
    else openHealth?.();
  }

  function dateRange() {
    if (!data.startDate || !days.length) return null;
    const locale = currentLocale();
    const start = dayDate(data.startDate, 1);
    const end = dayDate(data.startDate, days.length);
    const last = formatShortDate(end, locale);
    if (start === end) return last;
    // Same month: `16–17/01` (vi) or `16–17 Jan` (en).
    if (start.slice(0, 7) === end.slice(0, 7)) return `${Number(start.slice(8, 10)).toString().padStart(locale === 'vi' ? 2 : 1, '0')}–${last}`;
    return `${formatShortDate(start, locale)}–${last}`;
  }

  /* ---------------------------------------------------------------- Edits (op lists only; the server recalculates) */

  async function applyEdits(edits: PreviewEditOperation[]) {
    const outcome = await editor.apply(edits);
    if (outcome?.ok) setToast({ text: t('proposal.edit.updated', { revision: outcome.preview.preview_revision }), tone: 'info' });
    return outcome;
  }

  function moveStop(dayIndex: number, stopId: Uuid, direction: -1 | 1) {
    const day = days.find(item => item.day_index === dayIndex);
    const index = day?.stops.findIndex(stop => stop.id === stopId) ?? -1;
    if (!day || index < 0) return;
    const toOrdinal = index + 1 + direction;
    if (toOrdinal < 1 || toOrdinal > day.stops.length) return;
    void applyEdits([{ day_index: dayIndex, op: 'MOVE_STOP', stop_id: stopId, to_ordinal: toOrdinal }]);
  }

  const openEdit = useCallback((target: EditTarget) => {
    const day = days.find(item => item.stops.some(stop => stop.id === target.stopId));
    if (!day) return;
    setActiveDay(day.day_index);
    setOpenDay(day.day_index);
    setSelection(current => ({ ...current, [day.day_index]: target.stopId }));
    setEditTarget(target);
  }, [days]);

  // SCR-026 fix shortcuts and "Go to stop" hand over an intent, picked up when this screen regains focus.
  useFocusEffect(useCallback(() => {
    const intent = takeStopIntent(previewId);
    if (!intent) return;
    if (intent.kind === 'goto') { goToStop(intent.dayIndex, intent.stopId); return; }
    if (intent.focus === 'replace') {
      const stop = days.flatMap(item => item.stops).find(item => item.id === intent.stopId);
      if (stop) setPicker({ kind: 'replace', name: stop.name, number: stop.number, placeId: stop.place_id, stopId: stop.id });
      return;
    }
    openEdit({ focus: intent.focus, moveToStart: intent.moveToStart, stopId: intent.stopId });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days, openEdit, previewId]));

  const planned = useMemo(() => Object.fromEntries(days.flatMap(day => day.stops.map(stop => [stop.place_id, day.day_index] as const))), [days]);
  const pickerDay = picker?.kind === 'add' ? days.find(item => item.day_index === picker.dayIndex) : undefined;

  async function choosePlace(placeId: Uuid) {
    if (!picker || picker.kind === 'mustSee') return null;
    const edit: PreviewEditOperation = picker.kind === 'add'
      ? { day_index: picker.dayIndex, op: 'ADD_STOP', place_id: placeId }
      : { op: 'REPLACE_STOP', place_id: placeId, stop_id: picker.stopId };
    return applyEdits([edit]);
  }

  async function regenerated(preview: PlanPreview) {
    await onPreview(preview);
    setToast({ text: t('proposal.regen.done', { day: regenDay ?? 1, revision: preview.preview_revision }), tone: 'info' });
  }

  return <View style={st.screen}>
    <StatusBar style="light" />
    <ScrollView ref={scrollRef} contentContainerStyle={{ paddingBottom: data.readOnly ? insets.bottom + spacing.xxl : spacing.xxl }} showsVerticalScrollIndicator={false}>
      <View ref={contentRef} collapsable={false}>
        <ProposalHeader
          cityName={data.cityName}
          dateRange={dateRange()}
          dayCount={days.length}
          image={heroImage}
          imageLabel={heroLabel}
          onBack={goBack}
          saved={saved}
          stopCount={stopCount}
          title={t('proposal.title', { city, count: days.length })}
        />
        <View style={st.inner}>
          {data.health && <View style={[st.healthAction, st.pad]}>
            <HealthActionCard
              health={data.health}
              issues={issues}
              onReview={reviewIssues}
              reviewTargetsStop={!!firstStopIssue}
              updating={recalculating}
            />
          </View>}
          {day && <View style={st.section}>
            <SectionHeader style={st.pad} subtitle={days.length > 1 ? undefined : dateOf(day.day_index) ? t('proposal.day.tab', { date: dateOf(day.day_index), day: day.day_index }) : t('proposal.day.title', { day: day.day_index })} title={t('proposal.map.title')} />
            {days.length > 1 && <View style={st.tabs}><DayTabs activeDay={activeDay} dateOf={dateOf} days={days} onChange={showDay} /></View>}
            <View style={st.pad}>
              <ProposalMap
                day={day}
                onOpenPlace={placeId => router.push({ params: { placeId }, pathname: '/place/[placeId]' })}
                onSelect={stopId => select(day.day_index, stopId)}
                places={data.places}
                reducedMotion={reducedMotion}
                selectedStopId={selection[day.day_index] ?? null}
              />
            </View>
          </View>}

          <View style={[st.section, st.pad]}>
            <View style={st.itineraryHead}>
              <SectionHeader style={st.flex} subtitle={editing ? t('proposal.edit.modeHint') : t('proposal.itinerary.subtitle')} title={t('proposal.itinerary.title')} />
              {editable ? <PillButton
                accessibilityHint={t('proposal.edit.toggleHint')}
                icon={editing ? 'check' : 'edit'}
                label={editing ? t('proposal.edit.toggleDone') : t('proposal.edit.toggle')}
                onPress={() => setEditing(value => !value)}
                selected={editing}
              /> : null}
            </View>
            {editable ? <View style={st.status}>
              <EditStatusBanner
                offline={offline}
                onCreateAgain={() => router.push('/plan/new')}
                onDiscard={editor.discard}
                onRetry={() => { void editor.retry(); }}
                pending={pending}
                regenerating={regenerating}
              />
            </View> : null}
            <View style={st.days}>
              {days.map(item => <DayCard
                key={item.day_index}
                active={item.day_index === activeDay}
                cityName={city}
                date={dateOf(item.day_index)}
                day={item}
                onOpenPlace={placeId => router.push({ params: { placeId }, pathname: '/place/[placeId]' })}
                onSelectStop={stopId => { setActiveDay(item.day_index); select(item.day_index, stopId); }}
                onToggle={() => toggleDay(item.day_index)}
                open={openDay === item.day_index}
                places={data.places}
                reducedMotion={reducedMotion}
                registerRow={(stopId, view) => { rowRefs.current[stopId] = view; }}
                selectedStopId={selection[item.day_index] ?? null}
                edit={editable ? {
                  disabled: editDisabled,
                  editing,
                  onAddStop: () => setPicker({ dayIndex: item.day_index, kind: 'add' }),
                  onEditStop: stopId => openEdit({ stopId }),
                  onMoveStop: (stopId, direction) => moveStop(item.day_index, stopId, direction),
                  onRegenerate: regenerationEnabled ? () => setRegenDay(item.day_index) : undefined,
                  showLock: regenerationEnabled,
                } : undefined}
              />)}
            </View>
          </View>

          {data.health && <View ref={healthRef} collapsable={false} style={[st.section, st.pad]}>
            <HealthSummary
              health={data.health}
              issues={issues}
              onGoToStop={goToStop}
              onOpenDetail={data.previewId ? openHealth : undefined}
              updating={recalculating}
            />
          </View>}
        </View>
      </View>
    </ScrollView>

    {toast && <View accessibilityLiveRegion="polite" accessibilityRole="alert" style={[st.banner, elevation.lg, { top: insets.top + spacing.xs }]}>
      <View style={st.bannerIcon}><PlannerIcon color={colors.white} name={toast.tone === 'success' ? 'check' : 'refresh'} size={18} /></View>
      <Text style={st.bannerText}>{toast.text}</Text>
      <Pressable accessibilityLabel={t('proposal.save.dismiss')} accessibilityRole="button" hitSlop={4} onPress={() => setToast(null)} style={st.touch}>
        <PlannerIcon color={colors.deepOcean} name="close" size={18} />
      </Pressable>
    </View>}

    {editable ? <>
      <EditStopSheet
        allowedModes={data.allowedModes}
        days={days}
        offline={offline}
        onApply={applyEdits}
        onClose={() => setEditTarget(null)}
        onDiscardPending={editor.discard}
        onReplace={stop => {
          setEditTarget(null);
          // Let the sheet finish closing before the full-screen picker opens (stacked modals on iOS).
          setTimeout(() => setPicker({ kind: 'replace', name: stop.name, number: stop.number, placeId: stop.place_id, stopId: stop.id }), reducedMotion ? 50 : 350);
        }}
        onRetry={() => { void editor.retry(); }}
        pending={pending}
        places={data.places}
        target={editTarget}
      />
      <PlacePicker
        cityId={data.cityId}
        cityName={city}
        dayFull={!!pickerDay && pickerDay.stops.length >= MAX_STOPS_PER_DAY}
        mode={picker}
        offline={offline}
        onChoose={place => choosePlace(place.id)}
        onClose={() => setPicker(null)}
        planned={planned}
      />
      {regenerationEnabled ? <RegenerateDaySheet
        dayIndex={regenDay}
        days={days}
        offline={offline}
        onClose={() => setRegenDay(null)}
        onDone={regenerated}
        onRunningChange={setRegenerating}
        previewId={previewId}
        revision={data.previewRevision}
      /> : null}
    </> : null}

    {!data.readOnly && <SaveBar disabledReason={disabledReason} onOpenHealth={openHealth} onSave={save} saved={saved} />}
    {data.readOnly && data.tripId ? <View style={[st.bookBar, { paddingBottom: insets.bottom + spacing.sm }]}>
      <PrimaryButton icon="navigation" label={t('proposal.book')} onPress={() => setHandoffOpen(true)} />
    </View> : null}
    {!data.readOnly && previewId && data.previewRevision != null && data.health ? <SaveSheet
      healthReasons={data.healthReasons}
      onClose={() => setSaveOpen(false)}
      onFixPlan={openHealth}
      onSaved={() => { setSaved(true); setToast({ text: t('proposal.save.success'), tone: 'success' }); }}
      planHealth={data.health}
      previewId={previewId}
      previewRevision={data.previewRevision}
      summary={{
        cityCode: data.cityCode,
        cityName: data.cityName ?? '',
        dayCount: days.length,
        startDate: data.startDate ?? '',
        stopCount: days.reduce((sum, day) => sum + day.stops.length, 0),
        warningCount: data.healthReasons.filter(reason => reason.severity === 'WARNING').length,
        webUnverifiedStops: webUnverifiedStopNames(days),
      }}
      tripId={data.tripId ?? previewId}
      tripRevision={1}
      visible={saveOpen}
    /> : null}
    {data.tripId ? <HandoffSheet onClose={() => setHandoffOpen(false)} tripId={data.tripId} visible={handoffOpen} /> : null}
  </View>;
}

const st = StyleSheet.create({
  bookBar: { borderTopColor: colors.hairline, borderTopWidth: StyleSheet.hairlineWidth, backgroundColor: colors.white, paddingHorizontal: spacing.lg, paddingTop: spacing.sm },
  screen: { flex: 1, backgroundColor: colors.canvas },
  center: { alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  floatingBack: { position: 'absolute', left: spacing.md },
  touch: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  skeletonHero: { borderBottomLeftRadius: HERO_RADIUS, borderBottomRightRadius: HERO_RADIUS, overflow: 'hidden' },
  skeletonMeta: { paddingHorizontal: spacing.lg, marginTop: spacing.md },
  healthAction: { marginTop: spacing.md },
  skeletonBody: { gap: spacing.md, padding: spacing.lg },
  errorTile: { width: 72, height: 72, borderRadius: 36, backgroundColor: colors.surfaceTint, alignItems: 'center', justifyContent: 'center' },
  errorTitle: { ...typography.headline, textAlign: 'center', marginTop: spacing.md },
  errorBody: { ...typography.body, color: colors.textMuted, textAlign: 'center', marginTop: spacing.xxs },
  retry: { marginTop: spacing.xl, alignSelf: 'stretch' },
  inner: { width: '100%', maxWidth: 520, alignSelf: 'center' },
  flex: { flex: 1 },
  itineraryHead: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm },
  status: { gap: spacing.xs, marginBottom: spacing.sm },
  pad: { paddingHorizontal: spacing.lg },
  section: { marginTop: spacing.xxl },
  tabs: { marginBottom: spacing.sm },
  days: { gap: spacing.sm },
  banner: { position: 'absolute', left: spacing.md, right: spacing.md, flexDirection: 'row', alignItems: 'center', gap: 10, paddingLeft: spacing.sm, borderRadius: radii.inset, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.audioTeal },
  bannerIcon: { width: 28, height: 28, borderRadius: 14, backgroundColor: colors.tealText, alignItems: 'center', justifyContent: 'center' },
  bannerText: { flex: 1, fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.deepOcean, paddingVertical: spacing.sm },
});

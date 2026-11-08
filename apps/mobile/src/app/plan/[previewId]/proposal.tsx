/**
 * SCR-024 Proposal timeline + SCR-025 Proposal map, one screen showing the same revision (FR-088): a selection made on
 * the map or in the timeline is the same selection. Nothing here computes times, legs or Plan Health.
 *
 * Params: `previewId`; optional `tripId` and `mode=saved|draft` (from My trips). `mode=saved` shows the saved itinerary
 * read-only. Editing (SCR-027/028/030) sends op lists to the server and renders the revision it returns; pending edits
 * live in the draft store until acknowledged (ADR-009). After an explicit Save the screen is read-only.
 */
import { useCallback, useEffect, useMemo, useRef, useState, type ComponentRef } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { AiMark, Chip, CircleButton, Icon, PrimaryButton, Skeleton, StatusPill, Toast } from '../../../components/ui';
import { takeStopIntent } from '../../../features/planner/edit/draftStore';
import { EditStatusBanner } from '../../../features/planner/edit/EditStatusBanner';
import { EditStopSheet, type EditTarget } from '../../../features/planner/edit/EditStopSheet';
import { regenerationEnabled } from '../../../features/planner/edit/flags';
import { RegenerateDaySheet } from '../../../features/planner/edit/RegenerateDaySheet';
import { usePreviewEditor } from '../../../features/planner/edit/usePreviewEditor';
import { HealthPill } from '../../../features/planner/health/HealthPill';
import { collectIssues } from '../../../features/planner/health/reasons';
import { forgetReusableTrip } from '../../../features/planner/input/draftStore';
import { PlacePicker, type PickerMode } from '../../../features/planner/picker/PlacePicker';
import { useIsOffline } from '../../../features/home/useNetwork';
import { ProposalMap } from '../../../features/planner/map/ProposalMap';
import { Assumptions } from '../../../features/planner/timeline/Assumptions';
import { DateChips } from '../../../features/planner/timeline/DayTabs';
import { DayTimeline } from '../../../features/planner/timeline/DayTimeline';
import { ProposalHeader, proposalHeroHeight } from '../../../features/planner/timeline/ProposalHeader';
import { SaveBar } from '../../../features/planner/timeline/SaveBar';
import { dayDate, formatShortDate, formatTime, weekdayOf } from '../../../features/planner/timeline/format';
import { dayHasEstimate, EstimateLegend } from '../../../features/planner/timeline/TimeRail';
import { useProposal, type ProposalData } from '../../../features/planner/timeline/useProposal';
import { useReducedMotion } from '../../../hooks/useReducedMotion';
import { SaveSheet, webUnverifiedStopNames } from '../../../features/save';
import { HandoffSheet } from '../../../features/handoff';
import { currentLocale } from '../../../i18n';
import { MAX_STOPS_PER_DAY, type PreviewEditOperation } from '../../../lib/api/sourcePlanning';
import type { PlanPreview, TripDetail, Uuid } from '../../../lib/api/types';
import { CITY_IMAGES } from '../../../lib/images/cityImages';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';

type ViewElement = ComponentRef<typeof View>;
type WeekdayIndex = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export default function ProposalScreen() {
  const params = useLocalSearchParams<{ previewId: string; tripId?: string; mode?: string; ready?: string }>();
  const mode = params.mode === 'saved' || params.mode === 'draft' ? params.mode : undefined;
  const { state, reload, applyPreview, markSaved } = useProposal({ mode, previewId: params.previewId, tripId: params.tripId });
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();

  const goBack = () => (router.canGoBack() ? router.back() : router.replace('/home'));

  if (state.status === 'loading') {
    return <View accessibilityLabel={t('proposal.loading')} accessibilityLiveRegion="polite" style={st.screen}>
      <StatusBar style="light" />
      <Skeleton height={proposalHeroHeight(insets.top)} radius={0} />
      <View style={[st.floatingBack, { top: insets.top + spacing.xs }]}>
        <CircleButton accessibilityLabel={t('common.goBack')} icon="back" onPress={goBack} size={44} />
      </View>
      <View style={st.skeletonBody}>
        <Skeleton height={18} width={200} />
        <Skeleton height={32} radius={radii.pill} width={120} />
        <View style={st.skeletonChips}><Skeleton height={44} radius={radii.pill} width={150} /><Skeleton height={44} radius={radii.pill} width={150} /></View>
        <Skeleton height={220} radius={radii.card} />
        {[0, 1].map(key => <View key={key} style={st.skeletonRow}>
          <Skeleton height={28} radius={14} width={28} />
          <View style={st.flex}><Skeleton height={92} radius={radii.card} /></View>
        </View>)}
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
      <View style={st.errorTile}><Icon color={colors.primary} name={notFound ? 'map-pin' : 'warning'} size={30} /></View>
      <Text accessibilityLiveRegion="assertive" accessibilityRole="alert" style={st.errorTitle}>{t(notFound ? 'proposal.error.notFound' : 'proposal.error.generic')}</Text>
      <Text style={st.errorBody}>{t(notFound ? 'proposal.error.notFoundBody' : 'proposal.error.genericBody')}</Text>
      {!notFound && <PrimaryButton label={t('proposal.error.retry')} onPress={reload} style={st.retry} />}
    </View>;
  }

  return <Proposal data={state.data} goBack={goBack} justReady={params.ready === '1'} onPreview={applyPreview} onSaved={markSaved} previewId={params.previewId} />;
}

type ToastState = { text: string; tone: 'success' | 'info' };

function Proposal({ data, goBack, onPreview, onSaved, previewId: routePreviewId, justReady }: {
  data: ProposalData; goBack: () => void; onPreview: (preview: PlanPreview) => Promise<void>; onSaved: (trip: TripDetail) => void; previewId: Uuid; justReady: boolean;
}) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const reducedMotion = useReducedMotion();
  const scrollRef = useRef<ComponentRef<typeof ScrollView>>(null);
  const contentRef = useRef<ViewElement>(null);
  const rowRefs = useRef<Record<Uuid, ViewElement | null>>({});
  const { days } = data;

  const [activeDay, setActiveDay] = useState<number>(days[0]?.day_index ?? 1);
  // Selection is kept per day (SCR-024 "selection kept per day"); defaults to the day's first stop.
  const [selection, setSelection] = useState<Record<number, Uuid>>(() =>
    Object.fromEntries(days.filter(day => day.stops[0]).map(day => [day.day_index, day.stops[0].id])));
  // First arrival from `preview_ready`: say it is ready but not saved (Save stays explicit, ADR-009).
  const [toast, setToast] = useState<ToastState | null>(() => (justReady && !data.saved ? { text: t('proposal.ready.toast'), tone: 'info' } : null));
  const [saveOpen, setSaveOpen] = useState(false);
  const [handoffOpen, setHandoffOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null);
  const [picker, setPicker] = useState<PickerMode | null>(null);
  const [regenDay, setRegenDay] = useState<number | null>(null);
  const [regenerating, setRegenerating] = useState(false);
  const offline = useIsOffline();

  const previewId = data.previewId ?? routePreviewId;
  // Only an ACTIVE preview is a draft that can be edited and saved; SAVED/EXPIRED/DISCARDED are read-only.
  const editable = !data.readOnly && data.previewStatus === 'ACTIVE' && data.previewId != null && data.previewRevision != null;
  const closed = data.previewStatus === 'EXPIRED' || data.previewStatus === 'DISCARDED';
  const editor = usePreviewEditor({ onPreview, previewId, revision: data.previewRevision });
  const { pending } = editor;
  const recalculating = regenerating || pending?.status === 'applying';
  const editDisabled = offline || !!pending || regenerating;

  useEffect(() => { if (!editable) setEditing(false); }, [editable]);

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
    const timer = setTimeout(() => setToast(null), 3500);
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
  const hasRationale = days.some(item => item.stops.some(stop => !!stop.rationale));

  function dateOf(dayIndex: number) {
    return data.startDate ? formatShortDate(dayDate(data.startDate, dayIndex), currentLocale()) : '';
  }

  function weekdayOfDay(dayIndex: number) {
    return data.startDate ? weekdayOf(dayDate(data.startDate, dayIndex)) : null;
  }

  function scrollToView(view: ViewElement | null | undefined, offset = 96) {
    const content = contentRef.current;
    if (!view || !content) return;
    view.measureLayout(content, (_x: number, y: number) => {
      scrollRef.current?.scrollTo({ animated: !reducedMotion, y: Math.max(0, y - offset) });
    }, () => undefined);
  }

  const openPlace = (placeId: Uuid) => router.push({ params: { placeId }, pathname: '/place/[placeId]' });
  const registerRow = (stopId: Uuid, view: ViewElement | null) => { rowRefs.current[stopId] = view; };

  function select(dayIndex: number, stopId: Uuid) {
    setSelection(current => ({ ...current, [dayIndex]: stopId }));
  }

  function goToStop(dayIndex: number, stopId: Uuid) {
    setActiveDay(dayIndex);
    select(dayIndex, stopId);
    // Wait for the day to render before scrolling to the stop.
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

  const openHealth = data.previewId && data.health
    ? () => router.push({ params: { previewId: data.previewId as string }, pathname: '/plan/[previewId]/health' })
    : undefined;

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
    if (outcome?.ok) setToast({ text: t('proposal.edit.updated'), tone: 'info' });
    return outcome;
  }

  function moveStop(dayIndex: number, stopId: Uuid, direction: -1 | 1) {
    const target = days.find(item => item.day_index === dayIndex);
    const index = target?.stops.findIndex(stop => stop.id === stopId) ?? -1;
    if (!target || index < 0) return;
    const toOrdinal = index + 1 + direction;
    if (toOrdinal < 1 || toOrdinal > target.stops.length) return;
    void applyEdits([{ day_index: dayIndex, op: 'MOVE_STOP', stop_id: stopId, to_ordinal: toOrdinal }]);
  }

  const openEdit = useCallback((target: EditTarget) => {
    const owner = days.find(item => item.stops.some(stop => stop.id === target.stopId));
    if (!owner) return;
    setActiveDay(owner.day_index);
    setSelection(current => ({ ...current, [owner.day_index]: target.stopId }));
    setEditTarget(target);
  }, [days]);

  // SCR-026 fix shortcuts and "Go to stop" hand over an intent, picked up when this screen regains focus.
  useFocusEffect(useCallback(() => {
    const intent = takeStopIntent(previewId);
    if (!intent) return;
    if (intent.kind === 'goto') { goToStop(intent.dayIndex, intent.stopId); return; }
    if (!editable) return;
    if (intent.focus === 'replace') {
      const stop = days.flatMap(item => item.stops).find(item => item.id === intent.stopId);
      if (stop) setPicker({ kind: 'replace', name: stop.name, number: stop.number, placeId: stop.place_id, stopId: stop.id });
      return;
    }
    openEdit({ focus: intent.focus, moveToStart: intent.moveToStart, stopId: intent.stopId });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days, editable, openEdit, previewId]));

  const planned = useMemo(() => Object.fromEntries(days.flatMap(item => item.stops.map(stop => [stop.place_id, item.day_index] as const))), [days]);
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
    setToast({ text: t('proposal.regen.done', { day: regenDay ?? 1 }), tone: 'info' });
  }

  function saved(trip: TripDetail) {
    // Explicit Save done (API-022): read-only from now on, short confirmation, booking handoff in the bottom bar.
    onSaved(trip);
    forgetReusableTrip(trip.id);
    setSaveOpen(false);
    setEditing(false);
    setToast({ text: t('proposal.save.success'), tone: 'success' });
  }

  /* ---------------------------------------------------------------- Day header pieces */

  const dayTitle = day ? (() => {
    const date = dateOf(day.day_index);
    const weekday = weekdayOfDay(day.day_index);
    const when = date && weekday != null ? t('proposal.day.chip', { date, weekday: t(`planner.weekday.${weekday as WeekdayIndex}`) }) : '';
    return when ? t('proposal.day.chipLabel', { day: day.day_index, when }) : t('proposal.day.title', { day: day.day_index });
  })() : '';
  const dayFirst = formatTime(day?.stops[0]?.planned_arrival);
  const dayLast = formatTime(day?.stops[day.stops.length - 1]?.planned_departure);
  const daySummary = day ? [t('proposal.day.stops', { count: day.stops.length }), dayFirst && dayLast ? `${dayFirst} – ${dayLast}` : null].filter(Boolean).join(' · ') : '';

  const statusRow = data.saved
    ? <StatusPill icon="check" label={t('proposal.status.saved')} tone="success" />
    : closed
      ? <StatusPill icon="clock" label={t('proposal.status.expired')} tone="neutral" />
      : data.health
        ? <HealthPill health={data.health} onPress={openHealth} problems={issues.length} updating={recalculating} />
        : null;

  const bottomPad = editable || (data.saved && data.tripId) || closed ? spacing.xl : insets.bottom + spacing.xxl;

  return <View style={st.screen}>
    <StatusBar style="light" />
    <ScrollView ref={scrollRef} contentContainerStyle={{ paddingBottom: bottomPad }} showsVerticalScrollIndicator={false}>
      <View ref={contentRef} collapsable={false}>
        <ProposalHeader
          badge={data.saved ? null : closed ? null : { label: t('proposal.status.unsaved') }}
          dateRange={dateRange()}
          dayCount={days.length}
          image={heroImage}
          imageLabel={heroLabel}
          onBack={goBack}
          status={statusRow}
          stopCount={stopCount}
          title={data.title ?? t('proposal.title', { city, count: days.length })}
        />
        <View style={st.inner}>
          {closed ? <View accessibilityRole="alert" style={[st.pad, st.closed]}>
            <Icon color={colors.textSecondary} name="clock" size={20} />
            <View style={st.flex}>
              <Text style={st.closedTitle}>{t('proposal.closed.title')}</Text>
              <Text style={st.closedBody}>{t('proposal.closed.body')}</Text>
            </View>
          </View> : null}
          {data.assumptions.length ? <View style={st.pad}><Assumptions lines={data.assumptions} style={st.assumptions} /></View> : null}

          {day ? <View style={st.section}>
            {days.length > 1 ? <View style={st.tabs}>
              <DateChips activeDay={activeDay} dateOf={dateOf} days={days} onChange={setActiveDay} weekdayOf={weekdayOfDay} />
            </View> : null}
            <View style={st.pad}>
              <ProposalMap
                day={day}
                onOpenPlace={openPlace}
                onSelect={stopId => select(day.day_index, stopId)}
                places={data.places}
                reducedMotion={reducedMotion}
                selectedStopId={selection[day.day_index] ?? null}
              />
            </View>
          </View> : null}

          {day ? <View style={[st.section, st.pad]}>
            <View style={st.dayHead}>
              <View style={st.flex}>
                <Text accessibilityRole="header" style={st.dayTitle}>{dayTitle}</Text>
                <Text style={st.daySummary}>{daySummary}</Text>
              </View>
              {editable ? <Chip
                accessibilityLabel={editing ? t('proposal.edit.toggleDone') : t('proposal.edit.toggle')}
                icon={editing ? 'check' : 'edit'}
                label={editing ? t('proposal.edit.toggleDone') : t('proposal.edit.toggle')}
                onPress={() => setEditing(value => !value)}
                selected={editing}
              /> : null}
            </View>
            {dayHasEstimate(day) ? <EstimateLegend style={st.legend} /> : null}
            {editing ? <Text style={st.hint}>{t('proposal.edit.modeHint')}</Text> : null}
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
            {hasRationale ? <View style={st.aiLine}>
              <AiMark decorative size={14} />
              <Text style={st.aiText}>{t('proposal.ai.line')}</Text>
            </View> : null}
            <DayTimeline
              categoryNames={data.categoryNames}
              cityName={city}
              day={day}
              edit={editable ? {
                disabled: editDisabled,
                editing,
                onAddStop: () => setPicker({ dayIndex: day.day_index, kind: 'add' }),
                onEditStop: stopId => openEdit({ stopId }),
                onMoveStop: (stopId, direction) => moveStop(day.day_index, stopId, direction),
                onRegenerate: regenerationEnabled ? () => setRegenDay(day.day_index) : undefined,
                showLock: regenerationEnabled,
              } : undefined}
              onOpenPlace={openPlace}
              onSelectStop={stopId => select(day.day_index, stopId)}
              places={data.places}
              reducedMotion={reducedMotion}
              registerRow={registerRow}
              selectedStopId={selection[day.day_index] ?? null}
            />
          </View> : null}
        </View>
      </View>
    </ScrollView>

    {toast ? <View pointerEvents="box-none" style={[st.toast, { top: insets.top + spacing.xs }]}>
      <Toast onDismiss={() => setToast(null)} text={toast.text} tone={toast.tone} />
    </View> : null}

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
        onDiscardPending={editor.discard}
        onRetryPending={() => { void editor.retry(); }}
        pending={pending}
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
      <SaveBar disabledReason={disabledReason} onSave={() => setSaveOpen(true)} />
    </> : null}

    {data.saved && data.tripId ? <View style={[st.bottomBar, { paddingBottom: Math.max(insets.bottom, spacing.sm) + spacing.xs }]}>
      <PrimaryButton icon="navigation" label={t('proposal.book')} onPress={() => setHandoffOpen(true)} />
    </View> : closed ? <View style={[st.bottomBar, { paddingBottom: Math.max(insets.bottom, spacing.sm) + spacing.xs }]}>
      <PrimaryButton icon="refresh" label={t('proposal.edit.createAgain')} onPress={() => router.push('/plan/new')} />
    </View> : null}

    {editable && previewId && data.previewRevision != null && data.health ? <SaveSheet
      healthReasons={data.healthReasons}
      onClose={() => setSaveOpen(false)}
      onFixPlan={() => { setSaveOpen(false); openHealth?.(); }}
      onSaved={saved}
      planHealth={data.health}
      previewId={previewId}
      previewRevision={data.previewRevision}
      summary={{
        cityCode: data.cityCode,
        cityName: data.cityName ?? '',
        dayCount: days.length,
        startDate: data.startDate ?? '',
        stopCount,
        warningCount: issues.length,
        webUnverifiedStops: webUnverifiedStopNames(days),
      }}
      tripId={data.tripId ?? previewId}
      // The trip revision the preview was built on (a new trip is revision 0), never a guess (ADR-009).
      tripRevision={data.baseTripRevision ?? 0}
      visible={saveOpen}
    /> : null}
    {data.tripId && data.saved ? <HandoffSheet onClose={() => setHandoffOpen(false)} tripId={data.tripId} visible={handoffOpen} /> : null}
  </View>;
}

const st = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.canvas },
  center: { alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  flex: { flex: 1, minWidth: 0 },
  floatingBack: { position: 'absolute', left: spacing.md },
  skeletonBody: { gap: spacing.md, padding: spacing.lg },
  skeletonChips: { flexDirection: 'row', gap: spacing.xs },
  skeletonRow: { flexDirection: 'row', gap: spacing.sm },
  errorTile: { width: 72, height: 72, borderRadius: 36, backgroundColor: colors.primarySoft, alignItems: 'center', justifyContent: 'center' },
  errorTitle: { ...typography.headline, textAlign: 'center', marginTop: spacing.md },
  errorBody: { ...typography.body, color: colors.textMuted, textAlign: 'center', marginTop: spacing.xxs },
  retry: { marginTop: spacing.xl, alignSelf: 'stretch' },
  inner: { width: '100%', maxWidth: 560, alignSelf: 'center' },
  pad: { paddingHorizontal: spacing.lg },
  section: { marginTop: spacing.lg },
  tabs: { marginBottom: spacing.sm },
  assumptions: { marginTop: spacing.xs },
  closed: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.md, marginHorizontal: spacing.lg, padding: spacing.md, borderRadius: radii.card, backgroundColor: colors.surface },
  closedTitle: { ...typography.bodyStrong },
  closedBody: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textSecondary, marginTop: 2 },
  dayHead: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  dayTitle: { ...typography.headline },
  daySummary: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textSecondary, marginTop: 1 },
  legend: { marginTop: spacing.xxs },
  hint: { fontFamily: fonts.regular, fontSize: 13, lineHeight: 18, color: colors.textMuted, marginTop: spacing.xs },
  status: { gap: spacing.xs, marginTop: spacing.sm },
  aiLine: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: spacing.sm, marginBottom: spacing.sm },
  aiText: { flex: 1, fontFamily: fonts.regular, fontSize: 13, lineHeight: 18, color: colors.textMuted },
  toast: { position: 'absolute', left: spacing.md, right: spacing.md, alignItems: 'center' },
  bottomBar: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm, backgroundColor: colors.white, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.hairline },
});

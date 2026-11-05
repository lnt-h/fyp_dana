/**
 * SCR-024 Proposal timeline + SCR-025 Proposal map, one screen showing the same revision (FR-088): a selection made on
 * the map or in the timeline is the same selection. Nothing here computes times, legs or Plan Health.
 *
 * Params: `previewId`; optional `tripId` and `mode=saved|draft` (from My trips). `mode=saved` shows the saved itinerary
 * read-only. Fixture previews (EXPO_PUBLIC_USE_FIXTURES=1):
 *   /plan/00000000-0000-4000-8000-000000000501/proposal  WARNING
 *   /plan/00000000-0000-4000-8000-000000000502/proposal  BLOCKED (day-2 leg unavailable)
 */
import { useMemo, useRef, useState, type ComponentRef } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { CircleButton, Icon, PrimaryButton, SectionHeader, Skeleton } from '../../../components/ui';
import { HealthSummary } from '../../../features/planner/health/HealthSummary';
import { collectIssues } from '../../../features/planner/health/reasons';
import { ProposalMap } from '../../../features/planner/map/ProposalMap';
import { DayCard } from '../../../features/planner/timeline/DayCard';
import { DayTabs } from '../../../features/planner/timeline/DayTabs';
import { ProposalHeader } from '../../../features/planner/timeline/ProposalHeader';
import { SaveBar } from '../../../features/planner/timeline/SaveBar';
import { dayDate, formatShortDate } from '../../../features/planner/timeline/format';
import { PlannerIcon } from '../../../features/planner/timeline/icons';
import { useProposal, type ProposalData } from '../../../features/planner/timeline/useProposal';
import { useReducedMotion } from '../../../hooks/useReducedMotion';
import { currentLocale } from '../../../i18n';
import type { Uuid } from '../../../lib/api/types';
import { CITY_IMAGES } from '../../../lib/images/cityImages';
import { colors } from '../../../theme/colors';
import { elevation } from '../../../theme/elevation';
import { radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';

type ViewElement = ComponentRef<typeof View>;

export default function ProposalScreen() {
  const params = useLocalSearchParams<{ previewId: string; tripId?: string; mode?: string }>();
  const mode = params.mode === 'saved' || params.mode === 'draft' ? params.mode : undefined;
  const { state, reload } = useProposal({ mode, previewId: params.previewId, tripId: params.tripId });
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();

  const goBack = () => (router.canGoBack() ? router.back() : router.replace('/home'));

  if (state.status === 'loading') {
    return <View accessibilityLabel={t('proposal.loading')} accessibilityLiveRegion="polite" style={st.screen}>
      <StatusBar style="light" />
      <Skeleton height={312} radius={0} />
      <View style={[st.floatingBack, { top: insets.top + spacing.xs }]}>
        <CircleButton accessibilityLabel={t('common.goBack')} icon="back" onPress={goBack} size={44} />
      </View>
      <View style={st.skeletonStats}>
        {[0, 1, 2].map(index => <View key={index} style={st.skeletonStat}>
          <Skeleton height={60} radius={30} width={60} />
          <Skeleton height={16} width={56} />
        </View>)}
      </View>
      <View style={st.skeletonBody}>
        <Skeleton height={24} width={120} />
        <Skeleton height={220} radius={radii.card} />
        <Skeleton height={88} radius={radii.card} />
      </View>
    </View>;
  }

  if (state.status === 'error') {
    const notFound = state.code === 'not_found';
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

  return <Proposal data={state.data} goBack={goBack} />;
}

function Proposal({ data, goBack }: { data: ProposalData; goBack: () => void }) {
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
  const [showSuccess, setShowSuccess] = useState(false);

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
  const disabledReason = data.health === 'BLOCKED'
    ? t('proposal.save.blocked')
    : emptyDay ? t('proposal.save.emptyDay', { day: emptyDay.day_index }) : null;

  function save() {
    // Fixture only: the real Save (SCR-029 confirm, API-022 with Idempotency-Key) is a later step.
    setSaved(true);
    setShowSuccess(true);
  }

  const openHealth = data.health ? () => scrollToView(healthRef.current, 24) : undefined;

  return <View style={st.screen}>
    <StatusBar style="light" />
    <ScrollView ref={scrollRef} contentContainerStyle={{ paddingBottom: data.readOnly ? insets.bottom + spacing.xxl : spacing.xxl }} showsVerticalScrollIndicator={false}>
      <View ref={contentRef} collapsable={false}>
        <ProposalHeader
          cityName={data.cityName}
          dayCount={days.length}
          health={data.health}
          image={heroImage}
          imageLabel={heroLabel}
          onBack={goBack}
          onOpenHealth={() => openHealth?.()}
          saved={saved}
          stopCount={stopCount}
          title={t('proposal.title', { city, count: days.length })}
        />
        <View style={st.inner}>
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
            <SectionHeader subtitle={t('proposal.itinerary.subtitle')} title={t('proposal.itinerary.title')} />
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
              />)}
            </View>
          </View>

          {data.health && <View ref={healthRef} collapsable={false} style={[st.section, st.pad]}>
            <HealthSummary health={data.health} issues={issues} onGoToStop={goToStop} />
          </View>}
        </View>
      </View>
    </ScrollView>

    {showSuccess && <View accessibilityLiveRegion="polite" accessibilityRole="alert" style={[st.banner, elevation.lg, { top: insets.top + spacing.xs }]}>
      <View style={st.bannerIcon}><PlannerIcon color={colors.white} name="check" size={18} /></View>
      <Text style={st.bannerText}>{t('proposal.save.success')}</Text>
      <Pressable accessibilityLabel={t('proposal.save.dismiss')} accessibilityRole="button" hitSlop={4} onPress={() => setShowSuccess(false)} style={st.touch}>
        <PlannerIcon color={colors.deepOcean} name="close" size={18} />
      </Pressable>
    </View>}

    {!data.readOnly && <SaveBar disabledReason={disabledReason} onOpenHealth={openHealth} onSave={save} saved={saved} />}
  </View>;
}

const st = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.white },
  center: { alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  floatingBack: { position: 'absolute', left: spacing.md },
  touch: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  skeletonStats: { flexDirection: 'row', justifyContent: 'space-around', marginTop: spacing.lg },
  skeletonStat: { alignItems: 'center', gap: spacing.xs },
  skeletonBody: { gap: spacing.md, padding: spacing.lg },
  errorTile: { width: 72, height: 72, borderRadius: 36, backgroundColor: colors.skyWash, alignItems: 'center', justifyContent: 'center' },
  errorTitle: { ...typography.headline, textAlign: 'center', marginTop: spacing.md },
  errorBody: { ...typography.body, color: colors.textMuted, textAlign: 'center', marginTop: spacing.xxs },
  retry: { marginTop: spacing.xl, alignSelf: 'stretch' },
  inner: { width: '100%', maxWidth: 520, alignSelf: 'center' },
  pad: { paddingHorizontal: spacing.lg },
  section: { marginTop: spacing.xxl },
  tabs: { marginBottom: spacing.sm },
  days: { gap: spacing.sm },
  banner: { position: 'absolute', left: spacing.md, right: spacing.md, flexDirection: 'row', alignItems: 'center', gap: 10, paddingLeft: spacing.sm, borderRadius: radii.chip, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.audioTeal },
  bannerIcon: { width: 28, height: 28, borderRadius: 14, backgroundColor: colors.tealText, alignItems: 'center', justifyContent: 'center' },
  bannerText: { flex: 1, fontFamily: fonts.medium, fontSize: 14, lineHeight: 20, color: colors.deepOcean, paddingVertical: spacing.sm },
});

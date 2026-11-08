import { useCallback, useEffect, useRef, useState } from 'react';
import { Animated, Easing, StyleSheet, Text, View } from 'react-native';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { Icon, PhotoFallback, PrimaryButton, SecondaryButton, type IconName } from '../../../components/ui';
import { useReducedMotion } from '../../../hooks/useReducedMotion';
import { streamPlanning } from '../../../lib/api/source';
import { OPTIONAL_PLANNING_STAGES, PLANNING_STAGES, type ClarificationRequired, type ErrorDetail, type PlanningStage } from '../../../lib/api/types';
import { CITY_IMAGES } from '../../../lib/images/cityImages';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { setPendingView } from '../input/draftStore';
import { AssistantAvatar, Banner, IntroCard, PlannerShell, UserBubble, p, tone } from '../input/PlannerUI';
import { errorCopy, toErrorDetail } from './errorCopy';
import { getPlanRequest } from './planRequestStore';

const SLOW_AFTER_MS = 60_000;
/** Status lines per stage; rotation is cosmetic and never advances a stage. */
const STATUS_LINES = 2;
const ROTATE_MS = 3200;
const stageIcon: Record<PlanningStage, IconName> = {
  CHECKING_HEALTH: 'clock',
  RESEARCHING: 'search',
  ROUTING: 'navigation',
  SCHEDULING: 'calendar',
  SELECTING_PLACES: 'map-pin',
  VALIDATING_REQUEST: 'check',
  VERIFYING_WEB_PLACES: 'shield',
  WRITING: 'edit',
};

/** Steps shown: every stage except the research ones, which appear only once the server reports them. */
const visibleStages = (seenOptional: PlanningStage[]) =>
  PLANNING_STAGES.filter(stage => !OPTIONAL_PLANNING_STAGES.includes(stage) || seenOptional.includes(stage));
const ART_W = 196;
const ART_H = 228;

type Status =
  | { kind: 'running' }
  | { kind: 'clarify'; clarification: ClarificationRequired }
  | { kind: 'error'; error: ErrorDetail };

/** SCR-023: step list driven only by `progress.stage` events of the planning stream (API-018). */
export function GenerationProgressScreen() {
  const { t, i18n } = useTranslation();
  const reduceMotion = useReducedMotion();
  const request = getPlanRequest();
  /** Latest reported stage; the first row shows as current before any event (NFR-003). Stages never move back. */
  const [reached, setReached] = useState<PlanningStage>(PLANNING_STAGES[0]);
  const [seenOptional, setSeenOptional] = useState<PlanningStage[]>([]);
  const stages = visibleStages(seenOptional);
  const current = Math.max(0, stages.indexOf(reached));
  const [status, setStatus] = useState<Status>({ kind: 'running' });
  const [slow, setSlow] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const [line, setLine] = useState(0);
  const pulse = useRef(new Animated.Value(0)).current;

  const run = useCallback(() => {
    if (!request) return;
    controller.current?.abort();
    const abort = new AbortController();
    controller.current = abort;
    setReached(PLANNING_STAGES[0]);
    setSeenOptional([]);
    setSlow(false);
    setStatus({ kind: 'running' });
    // The slow line is informational only; it never advances a stage.
    const slowTimer = setTimeout(() => !abort.signal.aborted && setSlow(true), SLOW_AFTER_MS);
    streamPlanning(request.trip.id, request.body, event => {
      if (abort.signal.aborted) return;
      switch (event.type) {
        case 'progress': {
          const stage = event.stage;
          if (!PLANNING_STAGES.includes(stage)) break; // unknown stage from a newer server: ignore
          if (OPTIONAL_PLANNING_STAGES.includes(stage)) setSeenOptional(previous => (previous.includes(stage) ? previous : [...previous, stage]));
          setReached(previous => (PLANNING_STAGES.indexOf(stage) > PLANNING_STAGES.indexOf(previous) ? stage : previous));
          break;
        }
        case 'preview_ready':
          abort.abort();
          // `ready=1`: the proposal shows the one-time "ready, not saved yet" toast (Save stays explicit).
          router.replace({ params: { previewId: event.preview_id, ready: '1' }, pathname: '/plan/[previewId]/proposal' });
          break;
        case 'clarification_required':
          abort.abort();
          setStatus({ clarification: event.clarification, kind: 'clarify' });
          break;
        case 'error':
          abort.abort();
          if (event.error.code === 'unsupported_request') {
            setPendingView({ kind: 'unsupported' });
            router.replace('/plan/new');
          } else {
            setStatus({ error: event.error, kind: 'error' });
          }
          break;
      }
    }, abort.signal)
      .catch(error => { if (!abort.signal.aborted) setStatus({ error: toErrorDetail(error), kind: 'error' }); })
      .finally(() => clearTimeout(slowTimer));
  }, [request]);

  // Rotate the friendly status line within the current stage only.
  useEffect(() => {
    setLine(0);
    if (reduceMotion || status.kind !== 'running') return;
    const timer = setInterval(() => setLine(previous => (previous + 1) % STATUS_LINES), ROTATE_MS);
    return () => clearInterval(timer);
  }, [current, reduceMotion, status.kind]);

  // Soft halo pulse on the active step and the illustration; off under reduced motion.
  useEffect(() => {
    if (reduceMotion || status.kind !== 'running') { pulse.setValue(0); return; }
    const loop = Animated.loop(Animated.timing(pulse, { duration: 1600, easing: Easing.out(Easing.ease), toValue: 1, useNativeDriver: true }));
    loop.start();
    return () => { loop.stop(); pulse.setValue(0); };
  }, [pulse, reduceMotion, status.kind]);

  useEffect(() => {
    run();
    return () => controller.current?.abort();
  }, [run]);

  const editRequest = () => { controller.current?.abort(); router.replace('/plan/new'); };

  if (!request) {
    return <PlannerShell title={t('planner.title')} onBack={() => router.replace('/home')}
      footer={<PrimaryButton label={t('planner.progress.newTrip')} onPress={() => router.replace('/plan/new')} />}>
      <Banner tone="info">{t('planner.progress.missing')}</Banner>
    </PlannerShell>;
  }

  const cityName = i18n.resolvedLanguage === 'vi' ? request.city.name_vi : request.city.name_en;
  const title = t('planner.progress.title', { city: cityName });
  const media = CITY_IMAGES[request.city.code];
  const photo = resolveImage(media, { height: ART_H, width: ART_W });

  if (status.kind === 'clarify') {
    const { clarification } = status;
    return <PlannerShell title={t('planner.title')} onBack={editRequest}
      footer={<PrimaryButton icon="chevron-right" label={t('planner.progress.clarifyAction')} onPress={() => { setPendingView({ clarification, kind: 'clarify' }); router.replace('/plan/new'); }} />}>
      <Text accessibilityRole="header" style={styles.pageTitle}>{t('planner.progress.clarifyTitle')}</Text>
      <IntroCard label={t('planner.intro.label')} body={clarification.missing_fields.map(field => t(`planner.clarify.question.${field}`)).join(' ')} />
      {!!clarification.message && <Text style={p.hint}>{clarification.message}</Text>}
    </PlannerShell>;
  }

  if (status.kind === 'error') {
    const { error } = status;
    return <PlannerShell title={t('planner.title')} onBack={editRequest}
      footer={<>
        <PrimaryButton label={t('planner.errors.retry')} onPress={run} />
        <View style={styles.footerRow}>
          <SecondaryButton label={t('planner.errors.edit')} onPress={editRequest} style={p.flex} />
          <SecondaryButton label={t('planner.errors.home')} onPress={() => router.replace('/home')} style={p.flex} />
        </View>
      </>}>
      <View style={styles.errorHero}>
        <View style={styles.errorBadge}><Icon name="warning" size={34} color={tone.error} /></View>
        <Text accessibilityRole="header" style={styles.heading}>{t('planner.errors.title')}</Text>
        <Text style={styles.subtitle}>{title}</Text>
      </View>
      <Banner tone="error">
        <Text style={p.bannerBody}>{errorCopy(t, error.code)} {t('planner.errors.kept')}</Text>
        <Text style={styles.code}>{t('planner.errors.code', { code: error.code })}</Text>
      </Banner>
      {!!request.body.request_text && <UserBubble text={request.body.request_text} />}
    </PlannerShell>;
  }

  const currentStage = stages[current];
  const stepLabel = t('planner.progress.step', { current: current + 1, total: stages.length });
  const haloScale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.55] });
  const haloOpacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.45, 0] });
  const artScale = pulse.interpolate({ inputRange: [0, 0.5, 1], outputRange: [1, 1.04, 1] });

  return <PlannerShell centered title={t('planner.title')} onBack={editRequest}
    footer={<SecondaryButton label={t('planner.progress.cancel')} onPress={editRequest} />}>
    <View style={styles.hero}>
      <View style={styles.artWrap}>
        <Animated.View pointerEvents="none" style={[styles.artGlow, { transform: [{ scale: artScale }] }]} />
        <View style={styles.art}>
          {photo
            ? <Image source={photo.source} placeholder={photo.placeholder} placeholderContentFit="cover" contentFit="cover" transition={250} style={StyleSheet.absoluteFill}
              accessible accessibilityLabel={cityName} />
            : <PhotoFallback icon="map-pin" />}
        </View>
        <View style={styles.artAvatar}><AssistantAvatar size={52} /></View>
      </View>
      {photo && media?.attribution_text ? <Text numberOfLines={1} style={styles.credit}>{t('planner.city.photoCredit', { credit: media.attribution_text })}</Text> : null}

      <Text accessibilityRole="header" style={styles.heading}>{t('planner.progress.heading')}</Text>
      <Text style={styles.subtitle}>{t('planner.progress.subtitle', { city: cityName, count: request.trip.day_count })}</Text>
    </View>

    <View style={styles.stepsCard}>
      <View style={styles.stepsHead}>
        <Text accessibilityLiveRegion="polite" style={styles.stepCount}>{stepLabel}</Text>
        <View style={styles.bar} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          <View style={[styles.barFill, { width: `${((current + 1) / stages.length) * 100}%` }]} />
        </View>
      </View>
      <View accessibilityRole="list">
        {stages.map((stage, index) => {
          const state = index < current ? 'done' : index === current ? 'current' : 'pending';
          const label = t(`planner.progress.stages.${stage}`);
          const last = index === stages.length - 1;
          return <View key={stage} accessible accessibilityLabel={t(`planner.progress.state.${state}`, { label })}
            accessibilityLiveRegion={state === 'current' ? 'polite' : 'none'} style={styles.stepRow}>
            <View style={styles.rail}>
              <View style={styles.markerBox}>
                {state === 'current' && !reduceMotion && <Animated.View pointerEvents="none"
                  style={[styles.halo, { opacity: haloOpacity, transform: [{ scale: haloScale }] }]} />}
                <View style={[styles.marker, state === 'done' && styles.markerDone, state === 'current' && styles.markerCurrent]}>
                  <Icon name={state === 'done' ? 'check' : stageIcon[stage]} size={state === 'done' ? 18 : 20} strokeWidth={state === 'done' ? 2.6 : 1.8}
                    color={state === 'pending' ? colors.textMuted : colors.white} />
                </View>
              </View>
              {!last && <View style={[styles.connector, index < current && styles.connectorDone]} />}
            </View>
            <View style={[styles.stepCopy, !last && styles.stepCopyGap]}>
              <Text style={[styles.stepText, state === 'pending' && styles.stepPending, state === 'current' && styles.stepCurrent]}>{label}</Text>
              {state === 'current' && <Text style={styles.statusLine}>{t(`planner.progress.status.${currentStage}_${line === 0 ? 0 : 1}` as const)}</Text>}
            </View>
          </View>;
        })}
      </View>
    </View>

    {slow && <View accessibilityLiveRegion="polite" style={styles.slow}>
      <Icon name="clock" size={18} color={colors.deepOcean} />
      <Text style={styles.slowText}>{t('planner.progress.slow')}</Text>
    </View>}
    <Text style={styles.reassurance}>{t('planner.progress.reassurance')}</Text>
  </PlannerShell>;
}

const MARKER = 44;

const styles = StyleSheet.create({
  pageTitle: { ...typography.title, marginTop: spacing.xs, marginBottom: spacing.lg },
  hero: { alignItems: 'center', marginBottom: spacing.xl },
  artWrap: { width: ART_W + 24, height: ART_H + 24, alignItems: 'center', justifyContent: 'center' },
  artGlow: { position: 'absolute', width: ART_W + 24, height: ART_H + 24, borderTopLeftRadius: (ART_W + 24) / 2, borderTopRightRadius: (ART_W + 24) / 2, borderBottomLeftRadius: 40, borderBottomRightRadius: 40, backgroundColor: colors.surfaceTint },
  art: { width: ART_W, height: ART_H, borderTopLeftRadius: ART_W / 2, borderTopRightRadius: ART_W / 2, borderBottomLeftRadius: 30, borderBottomRightRadius: 30, overflow: 'hidden', backgroundColor: colors.deepOcean, borderWidth: 4, borderColor: colors.white },
  artAvatar: { position: 'absolute', bottom: 0, right: 8, borderRadius: 30, borderWidth: 4, borderColor: colors.white, backgroundColor: colors.white },
  credit: { fontFamily: fonts.medium, fontSize: 11, color: colors.textMuted, marginTop: 6, maxWidth: 280, textAlign: 'center' },
  heading: { ...typography.title, textAlign: 'center', marginTop: spacing.lg },
  subtitle: { fontFamily: fonts.regular, fontSize: 17, lineHeight: 24, color: colors.textMuted, textAlign: 'center', marginTop: 6 },
  stepsCard: { borderRadius: radii.card, backgroundColor: colors.white, borderWidth: 1, borderColor: tone.hairline, paddingHorizontal: 18, paddingTop: 16, paddingBottom: 18 },
  stepsHead: { marginBottom: spacing.md },
  stepCount: { ...typography.eyebrow, marginBottom: spacing.xs },
  bar: { height: 6, borderRadius: 3, backgroundColor: colors.surfaceTint, overflow: 'hidden' },
  barFill: { height: 6, borderRadius: 3, backgroundColor: colors.audioTeal },
  stepRow: { flexDirection: 'row', gap: 14 },
  rail: { width: MARKER, alignItems: 'center' },
  markerBox: { width: MARKER, height: MARKER, alignItems: 'center', justifyContent: 'center' },
  halo: { position: 'absolute', width: MARKER, height: MARKER, borderRadius: MARKER / 2, backgroundColor: colors.audioTeal },
  marker: { width: MARKER, height: MARKER, borderRadius: MARKER / 2, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surfaceTint },
  markerDone: { backgroundColor: colors.tealText },
  markerCurrent: { backgroundColor: colors.deepOcean },
  connector: { flex: 1, width: 2, minHeight: 14, borderRadius: 1, backgroundColor: colors.hairline, marginVertical: 4 },
  connectorDone: { backgroundColor: colors.audioTeal },
  stepCopy: { flex: 1, minHeight: MARKER, justifyContent: 'center', paddingTop: 2 },
  stepCopyGap: { paddingBottom: spacing.sm },
  stepText: { fontFamily: fonts.bold, fontSize: 16, lineHeight: 22, color: colors.ink },
  stepPending: { color: colors.textMuted, fontFamily: fonts.medium },
  stepCurrent: { color: colors.deepOcean },
  statusLine: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.tealText, marginTop: 2 },
  slow: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, alignSelf: 'center', marginTop: spacing.md, backgroundColor: colors.warnBg, borderRadius: radii.inset, paddingHorizontal: 14, paddingVertical: 10 },
  slowText: { fontFamily: fonts.bold, fontSize: 14, color: colors.deepOcean },
  reassurance: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textMuted, textAlign: 'center', marginTop: spacing.lg, paddingHorizontal: spacing.xs },
  footerRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  errorHero: { alignItems: 'center', marginTop: spacing.xl, marginBottom: spacing.xl },
  errorBadge: { width: 80, height: 80, borderRadius: 40, backgroundColor: colors.dangerBg, alignItems: 'center', justifyContent: 'center' },
  code: { fontFamily: fonts.medium, fontSize: 12, color: colors.textMuted, marginTop: 6 },
});

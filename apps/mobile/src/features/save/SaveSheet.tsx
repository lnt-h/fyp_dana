import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { useEffect, useRef, useState, type ComponentRef } from 'react';
import { useTranslation } from 'react-i18next';
import { AccessibilityInfo, Animated, Easing, Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon, PrimaryButton, SecondaryButton, type IconName } from '../../components/ui';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { stayPricesEnabled } from '../../lib/api/sourceTrips';
import type { City, CityCode, Conflict, HandoffKind, PlanHealth, PlanPreview, Trip, TripDetail, Uuid } from '../../lib/api/types';
import { CITY_IMAGES } from '../../lib/images/cityImages';
import { resolveImage } from '../../lib/images/imagekit';
import { colors } from '../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { HandoffPanel } from '../handoff/HandoffPanel';
import { HandoffIcon } from '../handoff/kindIcons';
import { useIsOffline } from '../home/useNetwork';
import { addIsoDays, cityName, formatShortDate } from './format';
import { SheetFrame } from './SheetFrame';
import { SuccessCheck } from './SuccessCheck';
import { useSaveTrip } from './useSaveTrip';

const errorText = '#AF3434';
const warnText = '#8A5800';

/** What the confirm card shows; build it with `saveSummaryFromPreview`. */
export type SaveSummary = {
  cityName: string;
  cityCode?: CityCode | null;
  startDate: string;
  dayCount: number;
  stopCount: number;
  warningCount: number;
};

/** Counts from the preview the user is looking at (no recomputation of health). */
export function saveSummaryFromPreview(preview: PlanPreview, trip: Pick<Trip, 'start_date' | 'day_count'>, city: City | null | undefined, isVi: boolean): SaveSummary {
  return {
    cityCode: city?.code ?? null,
    cityName: cityName(city, isVi),
    dayCount: trip.day_count,
    startDate: trip.start_date,
    stopCount: preview.days.reduce((sum, day) => sum + day.stops.length, 0),
    warningCount: (preview.health_reasons ?? []).filter(reason => reason.severity === 'WARNING').length,
  };
}

export type SaveSheetProps = {
  visible: boolean;
  tripId: Uuid;
  previewId: Uuid;
  /** `preview_revision` of the body on screen → `expected_preview_revision`. */
  previewRevision: number;
  /** Trip `revision` the draft is based on → `expected_trip_revision`. */
  tripRevision: number;
  planHealth: PlanHealth;
  /** Blocking reasons already known from the preview (shown without calling the API when health is BLOCKED). */
  healthReasons?: Conflict[];
  summary: SaveSummary;
  /** Fired once per successful save (also for an idempotent replay). Update caches/state here; keep the sheet open. */
  onSaved: (trip: TripDetail) => void;
  /** Close without changes. The draft is never discarded by this sheet. */
  onClose: () => void;
  /** "Xem chuyến đi". Default: close and open SCR-024 in saved mode. */
  onViewTrip?: (trip: TripDetail) => void;
  /** Conflict "Xem bản đã lưu". Default: close and open the saved trip. */
  onViewSaved?: () => void;
  /** Refused "Xem cách sửa" (→ SCR-026). Default: close. */
  onFixPlan?: () => void;
};

type View_ = { name: 'save' } | { name: 'handoff'; kinds: HandoffKind[] };

function openSavedTrip(tripId: Uuid) {
  router.push({ params: { mode: 'saved', previewId: tripId, tripId }, pathname: '/plan/[previewId]/proposal' });
}

/**
 * SCR-029 Save confirmation and result in one sheet: confirm → saving → success (with booking handoffs inline), or
 * refused / conflict / interrupted / expired / error. Explicit only; never dismissible mid-request.
 */
export function SaveSheet(props: SaveSheetProps) {
  const { visible, tripId, previewId, previewRevision, tripRevision, planHealth, healthReasons, summary, onSaved, onClose, onViewTrip, onViewSaved, onFixPlan } = props;
  const { t } = useTranslation();
  const offline = useIsOffline();
  const { state, save, retry, saveReplacing, reset } = useSaveTrip({ previewId, previewRevision, tripRevision });
  const [view, setView] = useState<View_>({ name: 'save' });
  const [confirmReplace, setConfirmReplace] = useState(false);
  const heading = useRef<ComponentRef<typeof Text>>(null);
  const reported = useRef<TripDetail | null>(null);

  // Fresh confirm each time the sheet opens, unless a save already succeeded.
  useEffect(() => {
    if (!visible) return;
    setView({ name: 'save' });
    setConfirmReplace(false);
    if (state.status !== 'success' && state.status !== 'saving') reset();
    const timer = setTimeout(() => {
      if (heading.current) AccessibilityInfo.sendAccessibilityEvent(heading.current, 'focus');
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  useEffect(() => {
    if (state.status === 'success' && reported.current !== state.trip) {
      reported.current = state.trip;
      onSaved(state.trip);
      AccessibilityInfo.announceForAccessibility(state.replayed ? t('save.success.replayed') : t('save.success.announce'));
    }
    if (state.status === 'error') AccessibilityInfo.announceForAccessibility(t('save.error.generic'));
    if (state.status === 'interrupted') AccessibilityInfo.announceForAccessibility(t('save.interrupted.body'));
  }, [onSaved, state, t]);

  const saving = state.status === 'saving';
  const blocked = planHealth === 'BLOCKED' && state.status === 'idle' ? { reasons: healthReasons ?? [] } : state.status === 'blocked' ? state : null;
  const close = () => { if (!saving) onClose(); };
  const viewTrip = (trip: TripDetail) => {
    if (onViewTrip) { onViewTrip(trip); return; }
    onClose();
    openSavedTrip(trip.id);
  };
  const viewSaved = () => {
    if (onViewSaved) { onViewSaved(); return; }
    onClose();
    openSavedTrip(tripId);
  };
  const fix = () => {
    if (onFixPlan) onFixPlan();
    else onClose();
  };

  /* ------------------------------------------------------------ Handoff (after success) */
  if (state.status === 'success' && view.name === 'handoff') {
    return (
      <SheetFrame
        accessibilityLabel={t('save.handoff.title')}
        footer={<SecondaryButton label={t('save.success.done')} onPress={onClose} style={styles.button} />}
        onRequestClose={() => setView({ name: 'save' })}
        visible={visible}
      >
        <HandoffPanel kinds={view.kinds} onBack={() => setView({ name: 'save' })} tripId={state.trip.id} />
      </SheetFrame>
    );
  }

  /* ------------------------------------------------------------ Success */
  if (state.status === 'success') {
    const { trip } = state;
    const start = formatShortDate(t, trip.start_date);
    const checkout = formatShortDate(t, addIsoDays(trip.start_date, trip.day_count));
    return (
      <SheetFrame
        accessibilityLabel={t('save.success.title')}
        footer={
          <>
            <PrimaryButton icon="chevron-right" iconPosition="end" label={t('save.success.viewTrip')} onPress={() => viewTrip(trip)} style={styles.button} variant="gradient" />
            <SecondaryButton disabled={offline} label={t('save.success.book')} onPress={() => setView({ kinds: ['STAY', 'ACTIVITY', 'TRANSPORT'], name: 'handoff' })} style={styles.button} />
          </>
        }
        onRequestClose={onClose}
        visible={visible}
      >
        <View accessibilityLiveRegion="polite" style={styles.successHead}>
          <SuccessCheck />
          <Text accessibilityRole="header" ref={heading} style={styles.successTitle}>{t('save.success.title')}</Text>
          <Text style={styles.successBody}>{t('save.success.body', { city: summary.cityName, count: trip.day_count })}</Text>
          {state.replayed ? (
            <View style={styles.replayed}>
              <Icon color={colors.tealText} name="check" size={16} />
              <Text style={styles.replayedText}>{t('save.success.replayed')}</Text>
            </View>
          ) : null}
        </View>
        <Text accessibilityRole="header" style={styles.cap}>{t('save.success.nextTitle')}</Text>
        <View style={styles.rows}>
          <HandoffEntry
            disabled={offline}
            kind="STAY"
            onPress={() => setView({ kinds: ['STAY'], name: 'handoff' })}
            subtitle={t('save.success.findStaySub', { city: summary.cityName, end: checkout, start })}
            title={t('save.success.findStay')}
          />
          <HandoffEntry
            disabled={offline}
            kind="TRANSPORT"
            onPress={() => setView({ kinds: ['TRANSPORT'], name: 'handoff' })}
            subtitle={t('save.success.findTransportSub', { start })}
            title={t('save.success.findTransport', { city: summary.cityName })}
          />
        </View>
      </SheetFrame>
    );
  }

  /* ------------------------------------------------------------ Refused (blocked) */
  if (blocked) {
    const reason = blocked.reasons.map(item => item.message).filter(Boolean).join(' · ') || t('save.blocked.fallbackReason');
    return (
      <SheetFrame
        accessibilityLabel={t('save.blocked.title')}
        footer={
          <>
            <PrimaryButton label={t('save.blocked.fix')} onPress={fix} style={styles.button} />
            <SecondaryButton label={t('save.blocked.close')} onPress={onClose} style={styles.button} />
          </>
        }
        onRequestClose={onClose}
        visible={visible}
      >
        <View accessibilityRole="alert" style={styles.stateHead}>
          <View style={[styles.stateIcon, { backgroundColor: '#FDECEA' }]}>
            <Icon color={errorText} name="blocked" size={28} />
          </View>
          <Text accessibilityRole="header" ref={heading} style={styles.title}>{t('save.blocked.title')}</Text>
          <Text style={styles.stateBody}>{t('save.blocked.body', { reason })}</Text>
        </View>
      </SheetFrame>
    );
  }

  /* ------------------------------------------------------------ Expired */
  if (state.status === 'expired') {
    return (
      <SheetFrame
        accessibilityLabel={t('save.expired.title')}
        footer={<PrimaryButton label={t('save.expired.action')} onPress={onClose} style={styles.button} />}
        onRequestClose={onClose}
        visible={visible}
      >
        <View accessibilityRole="alert" style={styles.stateHead}>
          <View style={[styles.stateIcon, { backgroundColor: colors.skyWash }]}>
            <Icon color={colors.tealText} name="clock" size={28} />
          </View>
          <Text accessibilityRole="header" ref={heading} style={styles.title}>{t('save.expired.title')}</Text>
          <Text style={styles.stateBody}>{t('save.expired.body')}</Text>
        </View>
      </SheetFrame>
    );
  }

  /* ------------------------------------------------------------ Confirm (+ saving, error, interrupted, conflict) */
  const interrupted = state.status === 'interrupted';
  const conflict = state.status === 'conflict' ? state : null;
  const primaryLabel = saving ? t('save.confirm.saving') : interrupted ? t('save.interrupted.retry') : t('save.confirm.save');
  const onPrimary = interrupted ? retry : save;

  return (
    <SheetFrame
      accessibilityLabel={t('save.confirm.title')}
      dismissible={!saving}
      footer={
        <>
          {conflict ? null : (
            <PrimaryButton
              disabled={offline || summary.stopCount === 0}
              icon={saving ? undefined : 'check'}
              label={primaryLabel}
              loading={saving}
              onPress={() => void onPrimary()}
              style={styles.button}
              variant="gradient"
            />
          )}
          <Pressable accessibilityRole="button" accessibilityState={{ disabled: saving }} disabled={saving} onPress={close} style={({ pressed }) => [styles.textLink, saving && styles.disabled, pressed && styles.pressed]}>
            <Text style={styles.textLinkText}>{t('save.confirm.keepEditing')}</Text>
          </Pressable>
        </>
      }
      onRequestClose={close}
      visible={visible}
    >
      <View>
        <Text style={styles.kicker}>{t('save.confirm.kicker')}</Text>
        <Text accessibilityRole="header" ref={heading} style={styles.title}>{t('save.confirm.title')}</Text>
      </View>

      <SummaryCard planHealth={planHealth} summary={summary} />

      {saving ? (
        <View accessibilityLiveRegion="polite" accessibilityRole="progressbar" style={styles.progress}>
          <ProgressBar />
          <Text style={styles.progressText}>{t('save.confirm.savingStatus')}</Text>
        </View>
      ) : null}

      {interrupted ? <Banner body={t('save.interrupted.body')} icon="warning" title={t('save.interrupted.title')} tone="warn" /> : null}
      {state.status === 'error' ? <Banner body={t('save.error.generic')} icon="warning" tone="error" /> : null}
      {offline && !saving ? <Banner body={t('save.handoff.offline')} icon="info" tone="info" /> : null}

      {conflict ? (
        <View accessibilityRole="alert" style={[styles.banner, styles.bannerWarn]}>
          <View style={styles.bannerRow}>
            <Icon color={warnText} name="warning" size={20} />
            <Text style={styles.bannerTitle}>{confirmReplace ? t('save.conflict.confirmTitle') : t('save.conflict.title')}</Text>
          </View>
          <Text style={styles.bannerBody}>{confirmReplace ? t('save.conflict.confirmBody') : t('save.conflict.body')}</Text>
          <View style={styles.bannerActions}>
            {confirmReplace ? (
              <>
                <PrimaryButton disabled={offline} label={t('save.conflict.confirm')} onPress={() => void saveReplacing(conflict.currentRevision)} style={styles.bannerButton} />
                <SecondaryButton label={t('save.conflict.cancel')} onPress={() => setConfirmReplace(false)} style={styles.bannerButton} />
              </>
            ) : (
              <>
                <SecondaryButton label={t('save.conflict.viewSaved')} onPress={viewSaved} style={styles.bannerButton} />
                <PrimaryButton disabled={offline} label={t('save.conflict.saveMine')} onPress={() => setConfirmReplace(true)} style={styles.bannerButton} />
              </>
            )}
          </View>
        </View>
      ) : null}

      <Text style={styles.note}>
        {t('save.confirm.note')}
        {stayPricesEnabled ? ` ${t('save.confirm.notePrices')}` : ''}
      </Text>
    </SheetFrame>
  );
}

/* ---------------------------------------------------------------- Pieces */

const HEALTH: Record<PlanHealth, { icon: IconName; color: string; bg: string }> = {
  BLOCKED: { bg: '#FDECEA', color: errorText, icon: 'blocked' },
  GOOD: { bg: '#E9F6EF', color: '#1E7A4C', icon: 'check' },
  WARNING: { bg: '#FFF5E4', color: warnText, icon: 'warning' },
};

function SummaryCard({ summary, planHealth }: { summary: SaveSummary; planHealth: PlanHealth }) {
  const { t } = useTranslation();
  const media = summary.cityCode ? CITY_IMAGES[summary.cityCode] : null;
  const photo = resolveImage(media, { height: 88, width: 88 });
  const start = formatShortDate(t, summary.startDate);
  const end = formatShortDate(t, addIsoDays(summary.startDate, summary.dayCount - 1));
  const dates = summary.dayCount === 1 ? start : `${start} – ${end}`;
  const days = t('save.confirm.days', { count: summary.dayCount });
  const stops = t('save.confirm.stops', { count: summary.stopCount });
  const health = HEALTH[planHealth];
  const healthText = planHealth === 'WARNING' && summary.warningCount > 0 ? t('save.confirm.warnings', { count: summary.warningCount }) : t(`save.confirm.health.${planHealth}`);

  return (
    <View accessible accessibilityLabel={t('save.confirm.summaryLabel', { city: summary.cityName, dates, days, health: healthText, stops })} style={styles.card}>
      <View style={styles.thumb}>
        {photo ? (
          <Image contentFit="cover" placeholder={photo.placeholder} source={photo.source} style={StyleSheet.absoluteFill} transition={200} />
        ) : (
          <LinearGradient colors={[colors.deepOcean, colors.tealDark]} end={{ x: 1, y: 1 }} start={{ x: 0, y: 0 }} style={StyleSheet.absoluteFill} />
        )}
      </View>
      <View style={styles.cardText}>
        <Text numberOfLines={1} style={styles.cardTitle}>{summary.cityName} · {days}</Text>
        <View style={styles.metaRow}>
          <Icon color={colors.textMuted} name="calendar" size={16} />
          <Text style={styles.meta}>{dates}</Text>
        </View>
        <View style={styles.pills}>
          <View style={styles.pill}>
            <Icon color={colors.tealText} name="map-pin" size={14} />
            <Text style={[styles.pillText, { color: colors.tealText }]}>{stops}</Text>
          </View>
          <View style={[styles.pill, { backgroundColor: health.bg }]}>
            <Icon color={health.color} name={health.icon} size={14} />
            <Text style={[styles.pillText, { color: health.color }]}>{healthText}</Text>
          </View>
        </View>
      </View>
    </View>
  );
}

function HandoffEntry({ kind, title, subtitle, disabled, onPress }: { kind: HandoffKind; title: string; subtitle: string; disabled: boolean; onPress: () => void }) {
  return (
    <Pressable
      accessibilityLabel={`${title}, ${subtitle}`}
      accessibilityRole="button"
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [styles.entry, disabled && styles.disabled, pressed && styles.entryPressed]}
    >
      <View style={styles.entryTile}>
        <HandoffIcon color={colors.deepOcean} name={kind} />
      </View>
      <View style={styles.entryText}>
        <Text style={styles.entryTitle}>{title}</Text>
        <Text style={styles.entrySub}>{subtitle}</Text>
      </View>
      <Icon color={colors.textMuted} name="chevron-right" size={20} />
    </Pressable>
  );
}

function Banner({ title, body, icon, tone }: { title?: string; body: string; icon: IconName; tone: 'warn' | 'error' | 'info' }) {
  const color = tone === 'error' ? errorText : tone === 'warn' ? warnText : colors.tealText;
  return (
    <View accessibilityRole="alert" style={[styles.banner, tone === 'warn' ? styles.bannerWarn : tone === 'error' ? styles.bannerError : styles.bannerInfo]}>
      <View style={styles.bannerRow}>
        <Icon color={color} name={icon} size={20} />
        <Text style={[title ? styles.bannerTitle : styles.bannerBody, styles.flex]}>{title ?? body}</Text>
      </View>
      {title ? <Text style={styles.bannerBody}>{body}</Text> : null}
    </View>
  );
}

/** Indeterminate progress line (sliding segment); a static full bar under reduced motion. */
function ProgressBar() {
  const reduced = useReducedMotion();
  const [width, setWidth] = useState(0);
  const sweep = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    if (reduced || width === 0) return;
    const loop = Animated.loop(Animated.timing(sweep, { duration: 1100, easing: Easing.inOut(Easing.cubic), toValue: 1, useNativeDriver: true }));
    loop.start();
    return () => { loop.stop(); sweep.setValue(0); };
  }, [reduced, sweep, width]);
  const translateX = sweep.interpolate({ inputRange: [0, 1], outputRange: [-width * 0.4, width] });
  return (
    <View onLayout={event => setWidth(event.nativeEvent.layout.width)} style={styles.track}>
      <Animated.View style={[reduced ? styles.fillFull : styles.fill, !reduced && { transform: [{ translateX }] }]}>
        <LinearGradient colors={[colors.teal, colors.audioTeal]} end={{ x: 1, y: 0 }} start={{ x: 0, y: 0 }} style={StyleSheet.absoluteFill} />
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: { borderRadius: radii.chip, gap: spacing.xs, padding: spacing.md },
  bannerActions: { gap: spacing.xs, marginTop: spacing.xs },
  bannerBody: { color: colors.ink, fontFamily: fonts.medium, fontSize: 14, lineHeight: 20 },
  bannerButton: { height: 52 },
  bannerError: { backgroundColor: '#FDECEA' },
  bannerInfo: { backgroundColor: colors.skyWash },
  bannerRow: { alignItems: 'center', flexDirection: 'row', gap: spacing.xs },
  bannerTitle: { color: colors.ink, flex: 1, fontFamily: fonts.bold, fontSize: 15, lineHeight: 20 },
  bannerWarn: { backgroundColor: '#FFF5E4' },
  button: { height: 56 },
  cap: { color: colors.textMuted, fontFamily: fonts.bold, fontSize: 12, letterSpacing: 1.2, textTransform: 'uppercase' },
  card: { alignItems: 'center', backgroundColor: '#F5FAFC', borderRadius: radii.card, flexDirection: 'row', gap: spacing.md, padding: spacing.sm },
  cardText: { flex: 1, gap: 4 },
  cardTitle: { ...typography.bodyStrong, fontSize: 17 },
  disabled: { opacity: 0.45 },
  entry: { alignItems: 'center', backgroundColor: colors.white, borderColor: '#DCE8EE', borderRadius: radii.card, borderWidth: 1, flexDirection: 'row', gap: spacing.sm, minHeight: 72, padding: spacing.sm },
  entryPressed: { backgroundColor: colors.skyWash },
  entrySub: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 14, lineHeight: 19 },
  entryText: { flex: 1 },
  entryTile: { alignItems: 'center', backgroundColor: colors.skyWash, borderRadius: radii.iconTile, height: 48, justifyContent: 'center', width: 48 },
  entryTitle: { ...typography.label, fontSize: 16 },
  fill: { borderRadius: 3, height: 6, overflow: 'hidden', width: '40%' },
  fillFull: { borderRadius: 3, height: 6, overflow: 'hidden', width: '100%' },
  flex: { flex: 1 },
  kicker: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 13, letterSpacing: 0.4, marginBottom: 2 },
  meta: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 14 },
  metaRow: { alignItems: 'center', flexDirection: 'row', gap: 6 },
  note: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 13, lineHeight: 19 },
  pill: { alignItems: 'center', backgroundColor: colors.skyWash, borderRadius: radii.pill, flexDirection: 'row', gap: 4, paddingHorizontal: 8, paddingVertical: 4 },
  pillText: { fontFamily: fonts.bold, fontSize: 12 },
  pills: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 2 },
  pressed: { opacity: 0.7 },
  progress: { gap: spacing.xs },
  progressText: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 14 },
  replayed: { alignItems: 'center', backgroundColor: colors.skyWash, borderRadius: radii.pill, flexDirection: 'row', gap: 6, marginTop: spacing.xs, paddingHorizontal: spacing.sm, paddingVertical: 6 },
  replayedText: { color: colors.ink, fontFamily: fonts.medium, fontSize: 13 },
  rows: { gap: spacing.sm },
  stateBody: { ...typography.body, color: colors.textMuted, textAlign: 'center' },
  stateHead: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.sm },
  stateIcon: { alignItems: 'center', borderRadius: 32, height: 64, justifyContent: 'center', width: 64 },
  successBody: { ...typography.body, color: colors.textMuted, textAlign: 'center' },
  successHead: { alignItems: 'center', gap: spacing.xs },
  successTitle: { ...typography.title, textAlign: 'center' },
  textLink: { alignItems: 'center', justifyContent: 'center', minHeight: MIN_TOUCH },
  textLinkText: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 16 },
  thumb: { backgroundColor: colors.deepOcean, borderRadius: 18, height: 88, overflow: 'hidden', width: 88 },
  title: { ...typography.title, fontSize: 26, lineHeight: 32 },
  track: { backgroundColor: colors.skyWash, borderRadius: 3, height: 6, overflow: 'hidden' },
});

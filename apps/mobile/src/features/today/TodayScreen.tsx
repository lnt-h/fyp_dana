import { Image } from 'expo-image';
import type { TFunction } from 'i18next';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AccessibilityInfo, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { CircleButton, GlassBadge, Icon, PhotoHero, PrimaryButton, SecondaryButton, Skeleton, travelModeIcon } from '../../components/ui';
import { ApiError, getPlace, getTrip, listCities } from '../../lib/api/source';
import type { City, Leg, Media, Stop, TripDetail, Uuid } from '../../lib/api/types';
import { CITY_IMAGES } from '../../lib/images/cityImages';
import { resolveImage } from '../../lib/images/imagekit';
import { colors } from '../../theme/colors';
import { elevation } from '../../theme/elevation';
import { MIN_TOUCH, radii, spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { ErrorBanner } from '../home/sections/SheetBanners';
import { openTripDetail, vietnamMinutesNow } from '../home/sections/homeSheetUtils';
import { addIsoDays, cityName, formatLongDate, formatShortDate } from '../save/format';
import { focusStop, legAfter, openDirections, pickDay, timeStops, type TimedStop } from './todayModel';

const FOCUS_PHOTO = 190;

type Load = { state: 'loading' } | { state: 'error'; notFound: boolean } | { state: 'ready'; trip: TripDetail; city: City | null };

/**
 * SCR-032 Today (`/trip/[tripId]/today`): today's stops of a saved trip in order. The featured stop and countdown come
 * from the itinerary's planned times compared with the clock; nothing is re-timed and no device location is read.
 */
export function TodayScreen({ tripId }: { tripId: Uuid }) {
  const { t, i18n } = useTranslation();
  const isVi = i18n.resolvedLanguage === 'vi';
  const insets = useSafeAreaInsets();
  const [load, setLoad] = useState<Load>({ state: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const [nowMinutes, setNowMinutes] = useState(() => vietnamMinutesNow());
  const [thumbs, setThumbs] = useState<Record<Uuid, Media | null>>({});
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let active = true;
    setLoad({ state: 'loading' });
    Promise.all([getTrip(tripId), listCities().catch(() => [] as City[])])
      .then(([trip, cities]) => { if (active) setLoad({ city: cities.find(item => item.id === trip.city_id) ?? null, state: 'ready', trip }); })
      .catch((error: unknown) => { if (active) setLoad({ notFound: error instanceof ApiError && error.status === 404, state: 'error' }); });
    return () => { active = false; };
  }, [tripId, attempt]);

  useEffect(() => {
    const timer = setInterval(() => setNowMinutes(vietnamMinutesNow()), 30_000);
    return () => clearInterval(timer);
  }, []);

  const picked = load.state === 'ready' ? pickDay(load.trip) : null;
  const day = load.state === 'ready' && picked ? load.trip.days.find(item => item.day_index === picked.dayIndex) : undefined;
  const stops = useMemo(() => (picked ? timeStops(day, picked.mode, nowMinutes) : []), [day, nowMinutes, picked]);
  const focus = focusStop(stops);
  const finished = picked?.mode === 'today' && stops.length > 0 && !focus;

  const placeIds = stops.map(item => item.stop.place_id).join(',');
  useEffect(() => {
    if (!placeIds) return;
    let active = true;
    Promise.all(placeIds.split(',').map(id => getPlace(id).then(place => [id, place.thumbnail] as const).catch(() => [id, null] as const)))
      .then(entries => { if (active) setThumbs(Object.fromEntries(entries)); });
    return () => { active = false; };
  }, [placeIds]);

  const directions = useCallback(async (stop: Stop) => {
    setNotice('');
    if (await openDirections(stop)) return;
    const message = t('save.today.directionsError');
    setNotice(message);
    AccessibilityInfo.announceForAccessibility(message);
    router.push({ params: { placeId: stop.place_id }, pathname: '/place/[placeId]' });
  }, [t]);

  const openPlace = (stop: Stop) => router.push({ params: { placeId: stop.place_id }, pathname: '/place/[placeId]' });
  const back = () => (router.canGoBack() ? router.back() : router.replace('/(tabs)/home'));
  const backButton = <CircleButton accessibilityLabel={t('save.today.back')} icon="back" onPress={back} />;

  if (load.state !== 'ready' || !picked) {
    return (
      <View style={styles.screen}>
        <PhotoHero height={300} image={null} title={t('save.today.title')} topLeft={backButton} />
        <View style={styles.body}>
          {load.state === 'error' ? (
            <ErrorBanner
              message={load.notFound ? t('save.today.notFound') : t('save.today.error')}
              onRetry={() => setAttempt(n => n + 1)}
              retryLabel={t('save.today.retry')}
            />
          ) : (
            <View accessibilityLabel={t('save.today.loading')} accessibilityRole="progressbar" style={styles.gap}>
              <Skeleton height={FOCUS_PHOTO + 150} radius={radii.card} />
              <Skeleton height={72} radius={radii.card} />
              <Skeleton height={72} radius={radii.card} />
            </View>
          )}
        </View>
      </View>
    );
  }

  const { trip, city } = load;
  const cityLabel = cityName(city, isVi);
  const dateIso = addIsoDays(trip.start_date, picked.dayIndex - 1);
  const subtitle = t('save.today.subtitle', { date: formatLongDate(t, dateIso), day: picked.dayIndex, total: trip.day_count });
  const heroImage = city ? CITY_IMAGES[city.code] : null;

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={{ paddingBottom: insets.bottom + spacing.xxl }} showsVerticalScrollIndicator={false}>
        <PhotoHero
          attribution={heroImage?.attribution_text}
          height={320}
          image={heroImage}
          kicker={cityLabel}
          title={picked.mode === 'today' ? t('save.today.title') : t('save.today.titleDay', { day: picked.dayIndex })}
          topLeft={backButton}
        >
          <View style={styles.heroMeta}>
            <GlassBadge icon="calendar" label={subtitle} />
            {stops.length ? <GlassBadge icon="map-pin" label={t('save.today.stopsCount', { count: stops.length })} /> : null}
          </View>
        </PhotoHero>

        <View style={styles.body}>
          {picked.mode !== 'today' ? (
            <View accessibilityRole="text" style={styles.info}>
              <Icon color={colors.tealText} name="info" size={20} />
              <Text style={styles.infoText}>
                {picked.mode === 'before'
                  ? t('save.today.startsOn', { date: formatShortDate(t, trip.start_date) })
                  : t('save.today.endedOn', { date: formatShortDate(t, addIsoDays(trip.start_date, trip.day_count - 1)) })}
              </Text>
            </View>
          ) : null}

          {stops.length === 0 ? (
            <StateCard body={t('save.today.emptyDayBody')} icon="map-pin" title={t('save.today.emptyDay')} />
          ) : null}

          {finished ? <StateCard body={t('save.today.finishedBody')} icon="lantern" title={t('save.today.finishedTitle')} /> : null}

          {focus ? (
            <FocusCard
              item={focus}
              mode={picked.mode}
              nowMinutes={nowMinutes}
              onDirections={() => void directions(focus.stop)}
              onOpen={() => openPlace(focus.stop)}
              thumb={thumbs[focus.stop.place_id] ?? null}
            />
          ) : null}

          {notice ? <Text accessibilityLiveRegion="polite" style={styles.notice}>{notice}</Text> : null}

          {stops.length ? (
            <View>
              <Text accessibilityRole="header" style={styles.sectionTitle}>{t('save.today.dayTitle')}</Text>
              <View role="list">
                {stops.map((item, index) => (
                  <TimelineRow
                    focused={item === focus}
                    focusLabel={item.status === 'current' ? t('save.today.now') : picked.mode === 'today' ? t('save.today.next') : t('save.today.first')}
                    item={item}
                    key={item.stop.id}
                    last={index === stops.length - 1}
                    leg={index < stops.length - 1 ? legAfter(day, item.stop) : undefined}
                    onDirections={() => void directions(item.stop)}
                    onOpen={() => openPlace(item.stop)}
                    thumb={thumbs[item.stop.place_id] ?? null}
                  />
                ))}
              </View>
            </View>
          ) : null}

          <Pressable accessibilityRole="link" onPress={() => openTripDetail(trip)} style={({ pressed }) => [styles.seeAll, pressed && styles.pressed]}>
            <Text style={styles.seeAllText}>{t('save.today.seeAll')}</Text>
            <Icon color={colors.tealText} name="chevron-right" size={18} />
          </Pressable>
        </View>
      </ScrollView>
    </View>
  );
}

/* ---------------------------------------------------------------- Pieces */

function useCountdown(item: TimedStop, mode: ReturnType<typeof pickDay>['mode'], nowMinutes: number): string {
  const { t } = useTranslation();
  if (item.status === 'current') return item.departure ? t('save.today.inProgress', { time: item.departure.label }) : t('save.today.now');
  if (!item.arrival) return '';
  if (mode !== 'today') return t('save.today.startsAt', { time: item.arrival.label });
  const diff = Math.max(0, item.arrival.minutes - nowMinutes);
  const h = Math.floor(diff / 60);
  const m = diff % 60;
  const duration = h === 0 ? t('save.today.minutes', { count: m }) : m === 0 ? t('save.today.hoursOnly', { count: h }) : t('save.today.hours', { h, m });
  return t('save.today.startsIn', { duration, time: item.arrival.label });
}

function FocusCard({ item, mode, nowMinutes, thumb, onDirections, onOpen }: { item: TimedStop; mode: ReturnType<typeof pickDay>['mode']; nowMinutes: number; thumb: Media | null; onDirections: () => void; onOpen: () => void }) {
  const { t } = useTranslation();
  const countdown = useCountdown(item, mode, nowMinutes);
  const photo = resolveImage(thumb, { height: FOCUS_PHOTO, width: 400 });
  const badge = item.status === 'current' ? t('save.today.now') : mode === 'today' ? t('save.today.next') : t('save.today.first');
  const { stop } = item;
  const showOther = stop.name !== stop.name_vi;
  return (
    <View style={[styles.focus, elevation.md]}>
      <View style={styles.focusClip}>
        <Pressable accessibilityHint={t('save.today.openPlace')} accessibilityLabel={`${badge}, ${stop.name}, ${countdown}`} accessibilityRole="button" onPress={onOpen} style={styles.focusPhoto}>
          {photo ? (
            <Image contentFit="cover" placeholder={photo.placeholder} placeholderContentFit="cover" source={photo.source} style={StyleSheet.absoluteFill} transition={200} />
          ) : (
            <LinearGradient colors={[colors.deepOcean, colors.tealDark]} end={{ x: 1, y: 1 }} start={{ x: 0, y: 0 }} style={StyleSheet.absoluteFill} />
          )}
          <LinearGradient colors={['rgba(7,21,30,0)', 'rgba(7,21,30,0.78)']} locations={[0.25, 1]} style={StyleSheet.absoluteFill} />
          <View style={[styles.focusBadge, item.status === 'current' && styles.focusBadgeNow]}>
            <Text style={[styles.focusBadgeText, item.status === 'current' && styles.focusBadgeTextNow]}>{badge}</Text>
          </View>
          <View style={styles.focusOverlay}>
            <Text numberOfLines={2} style={styles.focusName}>{stop.name}</Text>
            {showOther ? <Text numberOfLines={1} style={styles.focusOther}>{stop.name_vi}</Text> : null}
          </View>
        </Pressable>
        <View style={styles.focusBody}>
          <View accessibilityLiveRegion="polite" style={styles.countRow}>
            <View style={styles.countIcon}>
              <Icon color={colors.tealText} name="clock" size={20} />
            </View>
            <View style={styles.flex}>
              <Text style={styles.countText}>{countdown}</Text>
              {item.arrival && item.departure ? (
                <Text style={styles.countSub}>{t('save.today.visit', { end: item.departure.label, minutes: stop.visit_minutes, start: item.arrival.label })}</Text>
              ) : null}
            </View>
          </View>
          <View style={styles.actions}>
            <PrimaryButton icon="navigation" label={t('save.today.directions')} onPress={onDirections} style={styles.action} variant="gradient" />
            <SecondaryButton label={t('save.today.ask')} onPress={onOpen} style={styles.action} />
          </View>
        </View>
      </View>
    </View>
  );
}

function legText(t: TFunction, leg: Leg): string {
  if (leg.availability !== 'AVAILABLE' || leg.duration_s == null) return t('save.today.legUnavailable');
  const minutes = Math.max(1, Math.round(leg.duration_s / 60));
  return leg.travel_mode === 'WALK' ? t('save.today.legWalk', { minutes }) : t('save.today.legDrive', { minutes });
}

function TimelineRow({ item, thumb, focused, focusLabel, last, leg, onOpen, onDirections }: {
  item: TimedStop; thumb: Media | null; focused: boolean; focusLabel: string; last: boolean; leg?: Leg; onOpen: () => void; onDirections: () => void;
}) {
  const { t } = useTranslation();
  const { stop, status } = item;
  const done = status === 'done';
  const photo = resolveImage(thumb, { height: 56, width: 56 });
  const time = item.arrival?.label ?? '';
  const label = done ? t('save.today.doneLabel', { name: stop.name }) : `${focused ? `${focusLabel}, ` : ''}${t('save.today.stopLabel', { name: stop.name, time })}`;
  return (
    <View role="listitem">
      <View style={styles.row}>
        <View style={styles.rail}>
          <Text style={[styles.railTime, done && styles.muted]}>{time}</Text>
          <View style={[styles.dot, done && styles.dotDone, focused && styles.dotFocus]}>
            {done ? <Icon color={colors.white} name="check" size={12} strokeWidth={3} /> : null}
          </View>
          {!last ? <View style={styles.line} /> : null}
        </View>
        <Pressable
          accessibilityHint={t('save.today.openPlace')}
          accessibilityLabel={label}
          accessibilityRole="button"
          onPress={onOpen}
          style={({ pressed }) => [styles.rowCard, focused && styles.rowCardFocus, done && styles.rowCardDone, pressed && styles.rowPressed]}
        >
          <View style={styles.rowThumb}>
            {photo ? <Image contentFit="cover" source={photo.source} style={StyleSheet.absoluteFill} transition={150} /> : null}
          </View>
          <View style={styles.flex}>
            {focused ? <Text style={styles.rowBadge}>{focusLabel}</Text> : null}
            {done ? <Text style={styles.rowDone}>{t('save.today.done')}</Text> : null}
            <Text numberOfLines={2} style={[styles.rowName, done && styles.muted]}>{stop.name}</Text>
            {item.arrival && item.departure ? (
              <Text style={styles.rowSub}>{`${item.arrival.label} – ${item.departure.label}`}</Text>
            ) : null}
          </View>
          {!done ? (
            <CircleButton accessibilityLabel={t('save.today.directionsTo', { name: stop.name })} icon="navigation" onPress={onDirections} size={44} tone="tint" />
          ) : null}
        </Pressable>
      </View>
      {leg && !last ? (
        <View style={styles.legRow}>
          <View style={styles.rail}>
            <View style={styles.line} />
          </View>
          <View style={styles.legPill}>
            <Icon color={colors.textMuted} name={leg.availability === 'AVAILABLE' ? travelModeIcon(leg.travel_mode) : 'warning'} size={16} />
            <Text style={styles.legText}>{legText(t, leg)}</Text>
          </View>
        </View>
      ) : null}
    </View>
  );
}

function StateCard({ icon, title, body }: { icon: 'lantern' | 'map-pin'; title: string; body: string }) {
  return (
    <View accessibilityRole="summary" style={styles.stateCard}>
      <View style={styles.stateIcon}>
        <Icon color={colors.white} name={icon} size={28} />
      </View>
      <Text accessibilityRole="header" style={styles.stateTitle}>{title}</Text>
      <Text style={styles.stateBody}>{body}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  action: { flex: 1, height: 52, paddingHorizontal: spacing.sm },
  actions: { flexDirection: 'row', gap: spacing.sm },
  body: { gap: spacing.lg, paddingHorizontal: spacing.lg, paddingTop: spacing.xs },
  countIcon: { alignItems: 'center', backgroundColor: colors.skyWash, borderRadius: radii.iconTile, height: 44, justifyContent: 'center', width: 44 },
  countRow: { alignItems: 'center', flexDirection: 'row', gap: spacing.sm },
  countSub: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 14, lineHeight: 19 },
  countText: { ...typography.bodyStrong, fontSize: 17 },
  dot: { backgroundColor: colors.white, borderColor: colors.audioTeal, borderRadius: 9, borderWidth: 2.5, height: 18, marginTop: 6, width: 18, alignItems: 'center', justifyContent: 'center' },
  dotDone: { backgroundColor: colors.textMuted, borderColor: colors.textMuted },
  dotFocus: { backgroundColor: colors.audioTeal, borderColor: colors.skyWash, borderWidth: 4, height: 22, width: 22, borderRadius: 11 },
  flex: { flex: 1 },
  focus: { backgroundColor: colors.white, borderRadius: radii.card },
  focusBadge: { backgroundColor: colors.white, borderRadius: radii.pill, left: spacing.md, paddingHorizontal: 12, paddingVertical: 5, position: 'absolute', top: spacing.md },
  focusBadgeNow: { backgroundColor: colors.sun },
  focusBadgeText: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 13 },
  focusBadgeTextNow: { color: colors.ink },
  focusBody: { gap: spacing.md, padding: spacing.md },
  focusClip: { borderColor: '#DCE8EE', borderRadius: radii.card, borderWidth: StyleSheet.hairlineWidth, overflow: 'hidden' },
  focusName: { color: colors.white, fontFamily: fonts.bold, fontSize: 24, letterSpacing: -0.3, lineHeight: 30 },
  focusOther: { color: 'rgba(255,255,255,0.9)', fontFamily: fonts.medium, fontSize: 15, marginTop: 2 },
  focusOverlay: { bottom: 0, left: 0, padding: spacing.md, position: 'absolute', right: 0 },
  focusPhoto: { backgroundColor: colors.deepOcean, height: FOCUS_PHOTO },
  gap: { gap: spacing.md },
  heroMeta: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.xs },
  info: { alignItems: 'center', backgroundColor: colors.skyWash, borderRadius: radii.chip, flexDirection: 'row', gap: spacing.sm, padding: spacing.md },
  infoText: { color: colors.ink, flex: 1, fontFamily: fonts.medium, fontSize: 15, lineHeight: 21 },
  legPill: { alignItems: 'center', alignSelf: 'flex-start', flexDirection: 'row', gap: 6, marginVertical: spacing.xs, paddingVertical: 4 },
  legRow: { flexDirection: 'row', gap: spacing.sm },
  legText: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 13 },
  line: { backgroundColor: colors.mutedDot, flex: 1, marginTop: 4, minHeight: 12, width: 2 },
  muted: { color: colors.textMuted },
  notice: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 14, lineHeight: 20 },
  pressed: { opacity: 0.7 },
  rail: { alignItems: 'center', width: 48 },
  railTime: { color: colors.ink, fontFamily: fonts.bold, fontSize: 13 },
  row: { flexDirection: 'row', gap: spacing.sm },
  rowBadge: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 12, letterSpacing: 0.6, textTransform: 'uppercase' },
  rowCard: { alignItems: 'center', backgroundColor: colors.white, borderColor: '#DCE8EE', borderRadius: radii.card, borderWidth: 1, flex: 1, flexDirection: 'row', gap: spacing.sm, minHeight: 76, padding: spacing.xs, paddingRight: spacing.sm },
  rowCardDone: { backgroundColor: '#F5FAFC', borderColor: '#F5FAFC' },
  rowCardFocus: { borderColor: colors.audioTeal, borderWidth: 2 },
  rowDone: { color: colors.textMuted, fontFamily: fonts.bold, fontSize: 12 },
  rowName: { ...typography.label, fontSize: 16, lineHeight: 21 },
  rowPressed: { backgroundColor: colors.skyWash },
  rowSub: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, marginTop: 2 },
  rowThumb: { backgroundColor: colors.skyWash, borderRadius: radii.iconTile, height: 56, overflow: 'hidden', width: 56 },
  screen: { backgroundColor: colors.white, flex: 1 },
  sectionTitle: { ...typography.headline, marginBottom: spacing.sm },
  seeAll: { alignItems: 'center', alignSelf: 'center', flexDirection: 'row', gap: 4, minHeight: MIN_TOUCH, paddingHorizontal: spacing.md },
  seeAllText: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 16 },
  stateBody: { ...typography.body, color: colors.textMuted, textAlign: 'center' },
  stateCard: { alignItems: 'center', backgroundColor: '#F5FAFC', borderRadius: radii.card, gap: spacing.xs, padding: spacing.xl },
  stateIcon: { alignItems: 'center', backgroundColor: colors.deepOcean, borderRadius: 28, height: 56, justifyContent: 'center', marginBottom: spacing.xs, width: 56 },
  stateTitle: { ...typography.headline, textAlign: 'center' },
});

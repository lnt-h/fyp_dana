import { router } from 'expo-router';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Linking, Platform, StyleSheet, Text, View } from 'react-native';

import { GlassBadge, Icon, PrimaryButton, SecondaryButton, Skeleton } from '../../../components/ui';
import { getPlace, getTrip } from '../../../lib/api/source';
import type { CityCode, Media, Stop, Trip, TripDetail } from '../../../lib/api/types';
import { CITY_IMAGES } from '../../../lib/images/cityImages';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { elevation } from '../../../theme/elevation';
import { radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { todayInVietnam, tripStart } from '../../trips/tripDates';
import { ErrorBanner } from './SheetBanners';
import { timeOfDay, vietnamMinutesNow } from './homeSheetUtils';

const PHOTO_HEIGHT = 150;

/** 1-based day of the trip that is today in Asia/Ho_Chi_Minh (calendar-date difference only). */
function todayIndex(trip: Trip): number {
  return Math.round((todayInVietnam().getTime() - tripStart(trip).getTime()) / 86_400_000) + 1;
}

/** First stop of the day whose planned arrival (as given by the API) is later than now; null when the day is over. */
function nextStop(stops: Stop[], nowMinutes: number): { stop: Stop; time: string } | null {
  for (const stop of [...stops].sort((a, b) => a.ordinal - b.ordinal)) {
    const arrival = timeOfDay(stop.planned_arrival);
    if (arrival && arrival.minutes > nowMinutes) return { stop, time: arrival.label };
  }
  return null;
}

/** Opens the platform maps app with the stop's published coordinates (no device location involved). */
async function openDirections(stop: Stop): Promise<boolean> {
  const { latitude, longitude } = stop.location;
  const dest = `${latitude},${longitude}`;
  const apple = `http://maps.apple.com/?daddr=${dest}`;
  const google = `https://www.google.com/maps/dir/?api=1&destination=${dest}`;
  try {
    await Linking.openURL(Platform.OS === 'ios' ? apple : google);
    return true;
  } catch {
    try {
      await Linking.openURL(google);
      return true;
    } catch {
      return false;
    }
  }
}

type Load = { state: 'loading' } | { state: 'error' } | { state: 'ready'; detail: TripDetail };

/**
 * "Hôm nay" card (precursor of SCR-032): shown only while a saved trip covers today. Picks the next stop by comparing
 * the itinerary's own arrival times with the clock; never computes new times.
 */
export function TodayCard({ trip, cityCode, onOpenPlace }: { trip: Trip; cityCode: CityCode | null; onOpenPlace: (placeId: string) => void }) {
  const { t } = useTranslation();
  const [load, setLoad] = useState<Load>({ state: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const [nowMinutes, setNowMinutes] = useState(() => vietnamMinutesNow());
  const [thumb, setThumb] = useState<Media | null>(null);
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let active = true;
    setLoad({ state: 'loading' });
    getTrip(trip.id)
      .then(detail => { if (active) setLoad({ detail, state: 'ready' }); })
      .catch(() => { if (active) setLoad({ state: 'error' }); });
    return () => { active = false; };
  }, [trip.id, attempt]);

  useEffect(() => {
    const timer = setInterval(() => setNowMinutes(vietnamMinutesNow()), 60_000);
    return () => clearInterval(timer);
  }, []);

  const dayIndex = todayIndex(trip);
  const next = useMemo(() => {
    if (load.state !== 'ready') return null;
    const day = load.detail.days.find(item => item.day_index === dayIndex);
    return day ? nextStop(day.stops, nowMinutes) : null;
  }, [load, dayIndex, nowMinutes]);

  const nextPlaceId = next?.stop.place_id ?? null;
  useEffect(() => {
    setThumb(null);
    if (!nextPlaceId) return;
    let active = true;
    getPlace(nextPlaceId)
      .then(place => { if (active) setThumb(place.thumbnail); })
      .catch(() => undefined);
    return () => { active = false; };
  }, [nextPlaceId]);

  const directions = useCallback(async (stop: Stop) => {
    setNotice('');
    const ok = await openDirections(stop);
    if (!ok) {
      setNotice(t('homeSheet.today.directionsError'));
      onOpenPlace(stop.place_id);
    }
  }, [onOpenPlace, t]);

  if (load.state === 'loading') {
    return (
      <View accessibilityLabel={t('homeSheet.today.loading')} accessibilityRole="progressbar">
        <Skeleton height={PHOTO_HEIGHT + 112} radius={radii.card} />
      </View>
    );
  }
  if (load.state === 'error') {
    return <ErrorBanner message={t('homeSheet.today.error')} onRetry={() => setAttempt(n => n + 1)} retryLabel={t('homeSheet.today.retry')} />;
  }

  const media = thumb ?? (cityCode ? CITY_IMAGES[cityCode] : null);
  const photo = resolveImage(media, { height: PHOTO_HEIGHT, width: 400 });
  const kicker = t('homeSheet.today.kicker', { day: dayIndex });
  // SCR-032: the Today screen shows the rest of today and links to the full itinerary.
  const viewPlan = () => router.push({ pathname: '/trip/[tripId]/today', params: { tripId: trip.id } });

  return (
    <View style={[styles.card, elevation.md]}>
      <View style={styles.clip}>
        <View style={styles.photo}>
          {photo ? (
            <Image contentFit="cover" placeholder={photo.placeholder} placeholderContentFit="cover" source={photo.source} style={StyleSheet.absoluteFill} transition={200} />
          ) : (
            <LinearGradient colors={[colors.deepOcean, colors.tealDark]} end={{ x: 1, y: 1 }} start={{ x: 0, y: 0 }} style={StyleSheet.absoluteFill} />
          )}
          <LinearGradient colors={['rgba(7,21,30,0)', 'rgba(7,21,30,0.72)']} locations={[0.3, 1]} style={StyleSheet.absoluteFill} />
          <GlassBadge icon="calendar" label={kicker} style={styles.badge} />
          <View style={styles.overlay}>
            {next ? (
              <>
                <View style={styles.timeRow}>
                  <Icon color={colors.white} name="clock" size={16} />
                  <Text style={styles.time}>{t('homeSheet.today.next', { time: next.time })}</Text>
                </View>
                <Text numberOfLines={2} style={styles.name}>{next.stop.name}</Text>
              </>
            ) : (
              <Text numberOfLines={2} style={styles.name}>{t('homeSheet.today.done')}</Text>
            )}
          </View>
        </View>
        <View style={styles.body}>
          {!next ? <Text style={styles.doneBody}>{t('homeSheet.today.doneBody')}</Text> : null}
          {notice ? <Text accessibilityLiveRegion="polite" style={styles.notice}>{notice}</Text> : null}
          <View style={styles.actions}>
            {next ? (
              <PrimaryButton icon="navigation" label={t('homeSheet.today.directions')} onPress={() => void directions(next.stop)} style={styles.action} />
            ) : null}
            <SecondaryButton label={t('homeSheet.today.viewPlan')} onPress={viewPlan} style={styles.action} />
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  action: { flex: 1, height: 52, paddingHorizontal: spacing.sm },
  actions: { flexDirection: 'row', gap: spacing.sm },
  badge: { left: spacing.md, position: 'absolute', top: spacing.md },
  body: { gap: spacing.sm, padding: spacing.md },
  card: { backgroundColor: colors.white, borderRadius: radii.card },
  clip: { borderColor: '#DCE8EE', borderRadius: radii.card, borderWidth: StyleSheet.hairlineWidth, overflow: 'hidden' },
  doneBody: { ...typography.body, color: colors.textMuted, fontSize: 15, lineHeight: 21 },
  name: { color: colors.white, fontFamily: fonts.bold, fontSize: 22, letterSpacing: -0.2, lineHeight: 28 },
  notice: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18 },
  overlay: { bottom: 0, left: 0, padding: spacing.md, position: 'absolute', right: 0 },
  photo: { backgroundColor: colors.deepOcean, height: PHOTO_HEIGHT },
  time: { color: colors.white, fontFamily: fonts.bold, fontSize: 15 },
  timeRow: { alignItems: 'center', flexDirection: 'row', gap: 6, marginBottom: 2 },
});

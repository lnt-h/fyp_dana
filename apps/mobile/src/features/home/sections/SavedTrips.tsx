import { router } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { ScrollView } from 'react-native-gesture-handler';

import { Icon, PhotoCard, SectionHeader, Skeleton } from '../../../components/ui';
import { getTrip, type LoadErrorKind } from '../../../lib/api/source';
import type { City, Trip } from '../../../lib/api/types';
import { CITY_IMAGES } from '../../../lib/images/cityImages';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { formatTripDates } from '../../trips/tripDates';
import { ErrorBanner, NoticeBanner } from './SheetBanners';
import { cityLabel, openTripDetail } from './homeSheetUtils';

const CARD_WIDTH = 232;
const PHOTO_HEIGHT = 140;

export type TripsLoad = 'loading' | 'ready' | 'error';

/** Guest line in place of the section (SCR-008 Guest state). */
export function SavedTripsGuest({ onSignIn, gutter }: { onSignIn: () => void; gutter: number }) {
  const { t } = useTranslation();
  return (
    <Pressable
      accessibilityHint={t('homeSheet.trips.guestHint')}
      accessibilityRole="button"
      onPress={onSignIn}
      style={({ pressed }) => [styles.guest, { marginHorizontal: gutter }, pressed && styles.pressed]}
    >
      <View style={styles.guestIcon}><Icon color={colors.primary} name="calendar" size={22} /></View>
      <Text style={styles.guestText}>{t('homeSheet.trips.guest')}</Text>
      <Icon color={colors.primary} name="chevron-right" size={20} />
    </Pressable>
  );
}

/** "Chuyến đi của bạn": up to 3 saved trips as compact photo cards; hidden when there are none (SCR-008 Empty). */
export function SavedTrips({ trips, state, errorKind, cities, onRetry, gutter }: { trips: Trip[]; state: TripsLoad; errorKind?: LoadErrorKind | null; cities: City[]; onRetry: () => void; gutter: number }) {
  const { t, i18n } = useTranslation();
  const isVi = i18n.resolvedLanguage === 'vi';
  const [openingId, setOpeningId] = useState<string | null>(null);
  const [notice, setNotice] = useState('');

  if (state === 'ready' && trips.length === 0) return null;

  async function open(trip: Trip) {
    if (openingId) return;
    setOpeningId(trip.id); setNotice('');
    try {
      openTripDetail(await getTrip(trip.id));
    } catch {
      setNotice(t('homeSheet.trips.openError'));
    } finally {
      setOpeningId(null);
    }
  }

  const header = (
    <SectionHeader
      actionLabel={state === 'ready' ? t('homeSheet.trips.seeAll') : undefined}
      onAction={state === 'ready' ? () => router.push('/trips') : undefined}
      style={{ marginHorizontal: gutter }}
      title={t('homeSheet.trips.title')}
    />
  );

  if (state === 'loading') {
    return (
      <View>
        {header}
        <View accessibilityLabel={t('homeSheet.trips.loading')} accessibilityRole="progressbar" style={[styles.row, { paddingHorizontal: gutter }]}>
          <Skeleton height={PHOTO_HEIGHT} radius={radii.card} width={CARD_WIDTH} />
          <Skeleton height={PHOTO_HEIGHT} radius={radii.card} width={CARD_WIDTH} />
        </View>
      </View>
    );
  }

  if (state === 'error') {
    return (
      <View>
        {header}
        <View style={{ marginHorizontal: gutter }}>
          <ErrorBanner detail={errorKind ? t(`common.loadError.${errorKind}`) : null} message={t('homeSheet.trips.error')} onRetry={onRetry} retryLabel={t('homeSheet.trips.retry')} />
        </View>
      </View>
    );
  }

  return (
    <View>
      {header}
      {notice ? <View style={[styles.notice, { marginHorizontal: gutter }]}><NoticeBanner message={notice} /></View> : null}
      <ScrollView contentContainerStyle={[styles.row, { paddingHorizontal: gutter }]} horizontal showsHorizontalScrollIndicator={false}>
        {trips.slice(0, 3).map(trip => {
          const city = cities.find(item => item.id === trip.city_id);
          const name = cityLabel(city, isVi);
          return (
            <PhotoCard
              image={city ? CITY_IMAGES[city.code] : null}
              imageHeight={PHOTO_HEIGHT}
              key={trip.id}
              onPress={openingId ? undefined : () => void open(trip)}
              style={openingId === trip.id ? styles.opening : undefined}
              subtitle={formatTripDates(t, trip)}
              subtitleIcon="calendar"
              title={trip.title?.trim() || t('homeSheet.trips.card', { city: name, count: trip.day_count })}
              width={CARD_WIDTH}
            />
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  guest: { alignItems: 'center', backgroundColor: colors.surface, borderRadius: radii.card, flexDirection: 'row', gap: spacing.sm, minHeight: 64, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  guestIcon: { alignItems: 'center', backgroundColor: colors.white, borderRadius: radii.iconTile, height: MIN_TOUCH, justifyContent: 'center', width: MIN_TOUCH },
  guestText: { color: colors.ink, flex: 1, fontFamily: fonts.bold, fontSize: 15, lineHeight: 21 },
  notice: { marginBottom: spacing.sm },
  opening: { opacity: 0.6 },
  pressed: { opacity: 0.8 },
  row: { flexDirection: 'row', gap: spacing.sm, paddingBottom: spacing.sm },
});

import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon, PhotoFallback, Skeleton, StatusPill } from '../../components/ui';
import type { CityCode, Trip } from '../../lib/api/types';
import { CITY_IMAGES } from '../../lib/images/cityImages';
import { resolveImage } from '../../lib/images/imagekit';
import { colors } from '../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';

/** Cover photo height of a trip card (dp). */
const PHOTO_HEIGHT = 168;

/**
 * Per-trip duotone wash over the city cover (Wave 6 P2): every trip shares the one Đà Nẵng cover photo, so a
 * deterministic tint from the trip id tells cards apart at a glance. The first variant keeps the original look.
 */
const COVER_WASHES = ['rgba(22,33,43,0.35)', 'rgba(13,92,99,0.38)', 'rgba(122,58,44,0.32)'];

function coverWash(tripId: string): string {
  let hash = 0;
  for (let index = 0; index < tripId.length; index++) hash = (hash * 31 + tripId.charCodeAt(index)) >>> 0;
  return COVER_WASHES[hash % COVER_WASHES.length] ?? COVER_WASHES[0]!;
}

type Props = {
  trip: Trip;
  title: string;
  cityName: string;
  cityCode: CityCode | null;
  dates: string;
  isToday: boolean;
  opening: boolean;
  /** Card width in dp, used to size the ImageKit request. */
  width: number;
  onOpen: () => void;
  onDelete: () => void;
};

/**
 * Trip photo card (SCR-031, visual refresh): cover photo with a day-count chip, then title, dates and a status pill
 * (Saved / Draft, plus Today). The ⋯ button (and a long press) offers delete. No border; the photo carries the colour.
 */
export function TripCard({ trip, title, cityName, cityCode, dates, isToday, opening, width, onOpen, onDelete }: Props) {
  const { t } = useTranslation();
  const isDraft = trip.status === 'DRAFT';
  const status = isDraft ? t('trips.card.draft') : t('trips.card.saved');
  const cover = cityCode ? CITY_IMAGES[cityCode] : null;
  const photo = resolveImage(cover, { height: PHOTO_HEIGHT, width });
  const days = t('trips.card.days', { count: trip.day_count });

  return (
    <View style={styles.card}>
      <Pressable
        accessibilityHint={t('trips.card.hint')}
        accessibilityLabel={t('trips.card.label', { dates: `${dates}, ${days}`, status: isToday ? `${status}, ${t('trips.card.today')}` : status, title })}
        accessibilityRole="button"
        accessibilityState={{ busy: opening }}
        delayLongPress={450}
        disabled={opening}
        onLongPress={onDelete}
        onPress={onOpen}
        style={({ pressed }) => [pressed && styles.pressed]}
      >
        <View style={styles.photo}>
          {photo ? (
            <Image contentFit="cover" placeholder={photo.placeholder} placeholderContentFit="cover" source={photo.source} style={StyleSheet.absoluteFill} transition={200} />
          ) : (
            <PhotoFallback icon="suitcase" tone="dark" />
          )}
          <LinearGradient colors={[coverWash(trip.id), 'rgba(22,33,43,0)']} locations={[0, 0.45]} style={StyleSheet.absoluteFill} />
          <View style={styles.dayChip}>
            <Icon color={colors.ink} name="calendar" size={14} strokeWidth={2} />
            <Text maxFontSizeMultiplier={1.3} numberOfLines={1} style={styles.dayChipText}>{days}</Text>
          </View>
          {opening && <View style={styles.opening}><ActivityIndicator color={colors.white} /></View>}
          {photo && cover?.attribution_text ? <Text numberOfLines={1} style={styles.credit}>{cover.attribution_text}</Text> : null}
        </View>
        <View style={styles.body}>
          <Text numberOfLines={2} style={styles.title}>{title}</Text>
          <Text numberOfLines={1} style={styles.meta}>{[dates, cityName].filter(Boolean).join(' · ')}</Text>
          <View style={styles.pills}>
            <StatusPill icon={isDraft ? 'edit' : 'check'} label={status} tone={isDraft ? 'neutral' : 'success'} />
            {isToday && <StatusPill icon="navigation" label={t('trips.card.today')} tone="info" />}
          </View>
        </View>
      </Pressable>
      <Pressable
        accessibilityHint={t('trips.card.moreHint')}
        accessibilityLabel={t('trips.card.more', { title })}
        accessibilityRole="button"
        hitSlop={4}
        onPress={onDelete}
        style={({ pressed }) => [styles.more, pressed && styles.morePressed]}
      >
        <Icon color={colors.ink} name="more" size={20} />
      </Pressable>
    </View>
  );
}

/** Loading placeholder with the same geometry as `TripCard`. */
export function TripCardSkeleton() {
  return (
    <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.card}>
      <Skeleton height={PHOTO_HEIGHT} radius={radii.card} />
      <View style={styles.body}>
        <Skeleton height={20} radius={6} width="60%" />
        <Skeleton height={14} radius={6} style={{ marginTop: spacing.xs }} width="45%" />
        <Skeleton height={32} radius={radii.pill} style={{ marginTop: spacing.sm }} width={90} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  body: { paddingHorizontal: spacing.xxs, paddingTop: spacing.sm },
  card: { marginBottom: spacing.xl },
  credit: { bottom: 6, color: 'rgba(255,255,255,0.9)', fontFamily: fonts.medium, fontSize: 10, maxWidth: '60%', position: 'absolute', right: spacing.sm },
  dayChip: { alignItems: 'center', backgroundColor: colors.white, borderRadius: radii.pill, flexDirection: 'row', gap: 5, left: spacing.sm, minHeight: 30, paddingHorizontal: 10, position: 'absolute', top: spacing.sm },
  dayChipText: { color: colors.ink, fontFamily: fonts.semibold, fontSize: 13 },
  meta: { ...typography.label, color: colors.textSecondary, fontFamily: fonts.regular, marginTop: 2 },
  more: { alignItems: 'center', backgroundColor: colors.white, borderRadius: MIN_TOUCH / 2, height: MIN_TOUCH, justifyContent: 'center', position: 'absolute', right: spacing.sm, top: spacing.sm, width: MIN_TOUCH },
  morePressed: { backgroundColor: colors.surface },
  opening: { bottom: 0, left: 0, position: 'absolute', right: 0, top: 0, alignItems: 'center', backgroundColor: 'rgba(22,33,43,0.35)', justifyContent: 'center' },
  photo: { backgroundColor: colors.surface, borderRadius: radii.card, height: PHOTO_HEIGHT, overflow: 'hidden' },
  pills: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: spacing.sm },
  pressed: { opacity: 0.9, transform: [{ scale: 0.99 }] },
  title: { ...typography.headline },
});

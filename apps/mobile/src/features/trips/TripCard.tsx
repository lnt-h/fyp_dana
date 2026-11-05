import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { GlassBadge, Icon, Skeleton, type IconName, PhotoFallback } from '../../components/ui';
import type { CityCode, Trip } from '../../lib/api/types';
import { CITY_IMAGES } from '../../lib/images/cityImages';
import { resolveImage } from '../../lib/images/imagekit';
import { colors } from '../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../theme/spacing';
import { fonts } from '../../theme/typography';

/** Photo area height of a trip card (dp). */
const PHOTO_HEIGHT = 190;
const hairline = colors.hairline;
/** Warm wash for Draft / Today pills; ink text on it is > 15:1. */
const sunWash = colors.warnBg;

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

function StatusPill({ icon, label, tone }: { icon: IconName; label: string; tone: 'saved' | 'draft' | 'today' }) {
  const fg = tone === 'saved' ? colors.ok : colors.ink;
  return (
    <View style={[styles.pill, tone === 'saved' ? styles.pillSaved : styles.pillWarm]}>
      <Icon color={tone === 'today' ? colors.ink : fg} name={icon} size={14} strokeWidth={2} />
      <Text numberOfLines={1} style={[styles.pillText, { color: fg }]}>{label}</Text>
    </View>
  );
}

/** Photo-led trip card (SCR-031): city photo with title overlay, day badge, ⋯ delete, white footer with dates and status. */
export function TripCard({ trip, title, cityName, cityCode, dates, isToday, opening, width, onOpen, onDelete }: Props) {
  const { t } = useTranslation();
  const isDraft = trip.status === 'DRAFT';
  const status = isDraft ? t('trips.card.draft') : t('trips.card.saved');
  const cover = cityCode ? CITY_IMAGES[cityCode] : null;
  const photo = resolveImage(cover, { height: PHOTO_HEIGHT, width });

  return (
    <View style={styles.card}>
      <Pressable
        accessibilityHint={t('trips.card.hint')}
        accessibilityLabel={t('trips.card.label', { dates, status: isToday ? `${status}, ${t('trips.card.today')}` : status, title })}
        accessibilityRole="button"
        accessibilityState={{ busy: opening }}
        delayLongPress={450}
        disabled={opening}
        onLongPress={onDelete}
        onPress={onOpen}
        style={({ pressed }) => [styles.clip, pressed && styles.pressed]}
      >
        <View style={styles.photo}>
          {photo ? (
            <Image contentFit="cover" placeholder={photo.placeholder} placeholderContentFit="cover" source={photo.source} style={StyleSheet.absoluteFill} transition={200} />
          ) : (
            <PhotoFallback tone="dark" icon="calendar" />
          )}
          <LinearGradient colors={['rgba(7,21,30,0.28)', 'rgba(7,21,30,0)', 'rgba(7,21,30,0.78)']} locations={[0, 0.35, 1]} style={StyleSheet.absoluteFill} />
          <GlassBadge icon="calendar" label={t('trips.card.days', { count: trip.day_count })} style={styles.badge} />
          <View style={styles.overlay}>
            <Text numberOfLines={2} style={styles.title}>{title}</Text>
            {!!cityName && (
              <View style={styles.cityRow}>
                <Icon color={colors.white} name="map-pin" size={16} />
                <Text numberOfLines={1} style={styles.city}>{cityName}</Text>
              </View>
            )}
          </View>
          {photo && cover?.attribution_text ? <Text numberOfLines={1} style={styles.credit}>{cover.attribution_text}</Text> : null}
        </View>
        <View style={styles.footer}>
          <View style={styles.footerMain}>
            <View style={styles.dateRow}>
              <Icon color={colors.textMuted} name="calendar" size={17} />
              <Text numberOfLines={1} style={styles.dates}>{dates}</Text>
            </View>
            <View style={styles.pills}>
              <StatusPill icon={isDraft ? 'clock' : 'check'} label={status} tone={isDraft ? 'draft' : 'saved'} />
              {isToday && <StatusPill icon="navigation" label={t('trips.card.today')} tone="today" />}
            </View>
          </View>
          <View style={styles.view}>
            {opening ? (
              <>
                <ActivityIndicator color={colors.tealText} size="small" />
                <Text style={styles.viewText}>{t('trips.card.opening')}</Text>
              </>
            ) : (
              <>
                <Text style={styles.viewText}>{t('trips.card.view')}</Text>
                <Icon color={colors.tealText} name="chevron-right" size={18} strokeWidth={2.2} />
              </>
            )}
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
        <Icon color={colors.white} name="more" size={22} />
      </Pressable>
    </View>
  );
}

/** Loading placeholder with the same geometry as `TripCard`. */
export function TripCardSkeleton() {
  return (
    <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.card}>
      <View style={styles.clip}>
        <Skeleton height={PHOTO_HEIGHT} radius={0} />
        <View style={styles.footer}>
          <View style={styles.footerMain}>
            <Skeleton height={14} width="70%" radius={7} />
            <Skeleton height={28} style={{ marginTop: spacing.sm }} width={92} radius={radii.chip} />
          </View>
          <Skeleton height={14} width={48} radius={7} />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { position: 'absolute', right: spacing.sm, top: spacing.sm },
  card: { backgroundColor: colors.white, borderRadius: radii.photoCard, marginBottom: spacing.lg },
  city: { color: colors.white, flexShrink: 1, fontFamily: fonts.regular, fontSize: 15, lineHeight: 20 },
  cityRow: { alignItems: 'center', flexDirection: 'row', gap: 5, marginTop: 4 },
  clip: { backgroundColor: colors.white, borderColor: hairline, borderRadius: radii.photoCard, borderWidth: StyleSheet.hairlineWidth, overflow: 'hidden' },
  credit: { bottom: 6, color: 'rgba(255,255,255,0.85)', fontFamily: fonts.medium, fontSize: 10, maxWidth: '60%', position: 'absolute', right: spacing.sm },
  dateRow: { alignItems: 'center', flexDirection: 'row', gap: 8 },
  dates: { color: colors.textMuted, flexShrink: 1, fontFamily: fonts.regular, fontSize: 15, lineHeight: 20 },
  footer: { alignItems: 'center', flexDirection: 'row', gap: spacing.sm, paddingHorizontal: spacing.md, paddingVertical: 14 },
  footerMain: { flex: 1 },
  more: {
    alignItems: 'center',
    backgroundColor: 'rgba(7,21,30,0.55)',
    borderColor: 'rgba(255,255,255,0.28)',
    borderRadius: MIN_TOUCH / 2,
    borderWidth: StyleSheet.hairlineWidth,
    height: MIN_TOUCH,
    justifyContent: 'center',
    left: spacing.sm,
    position: 'absolute',
    top: spacing.sm,
    width: MIN_TOUCH,
  },
  morePressed: { backgroundColor: 'rgba(7,21,30,0.75)' },
  overlay: { bottom: 0, left: 0, paddingBottom: 22, paddingHorizontal: spacing.md, position: 'absolute', right: 0 },
  photo: { backgroundColor: colors.deepOcean, height: PHOTO_HEIGHT },
  pill: { alignItems: 'center', alignSelf: 'flex-start', borderRadius: radii.chip, flexDirection: 'row', gap: 5, minHeight: 28, paddingHorizontal: 10 },
  pillSaved: { backgroundColor: colors.okBg },
  pillText: { fontFamily: fonts.bold, fontSize: 13, lineHeight: 18 },
  pillWarm: { backgroundColor: sunWash },
  pills: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 10 },
  pressed: { opacity: 0.94, transform: [{ scale: 0.99 }] },
  title: { color: colors.white, fontFamily: fonts.bold, fontSize: 24, letterSpacing: -0.5, lineHeight: 30 },
  view: { alignItems: 'center', alignSelf: 'stretch', flexDirection: 'row', gap: 2, minHeight: MIN_TOUCH, paddingLeft: spacing.xs },
  viewText: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 15 },
});

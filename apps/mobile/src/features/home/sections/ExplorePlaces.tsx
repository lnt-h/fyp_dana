import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { ScrollView } from 'react-native-gesture-handler';

import { Icon, SectionHeader, Skeleton, categoryIcon } from '../../../components/ui';
import type { Place } from '../../../lib/api/types';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { elevation } from '../../../theme/elevation';
import { radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { ErrorBanner } from './SheetBanners';

const CARD_WIDTH = 160;
const CARD_HEIGHT = 200;

export type PlacesLoad = 'loading' | 'ready' | 'error';

function PlaceTile({ place, onPress }: { place: Place; onPress: () => void }) {
  const { t } = useTranslation();
  const photo = resolveImage(place.thumbnail, { height: CARD_HEIGHT, width: CARD_WIDTH });
  const minutes = place.visit_minutes_suggested ? t('homeSheet.explore.minutes', { count: place.visit_minutes_suggested }) : null;
  return (
    <Pressable
      accessibilityLabel={[place.name, minutes].filter(Boolean).join(', ')}
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.tile, elevation.sm, pressed && styles.pressed]}
    >
      <View style={styles.clip}>
        {photo ? (
          <Image contentFit="cover" placeholder={photo.placeholder} placeholderContentFit="cover" source={photo.source} style={StyleSheet.absoluteFill} transition={200} />
        ) : (
          <LinearGradient colors={[colors.deepOcean, colors.tealDark]} end={{ x: 1, y: 1 }} start={{ x: 0, y: 0 }} style={StyleSheet.absoluteFill} />
        )}
        <LinearGradient colors={['rgba(7,21,30,0)', 'rgba(7,21,30,0.78)']} locations={[0.35, 1]} style={StyleSheet.absoluteFill} />
        <View style={styles.overlay}>
          <Text numberOfLines={2} style={styles.name}>{place.name}</Text>
          <View style={styles.meta}>
            <Icon color={colors.white} name={categoryIcon(place.category_code)} size={15} />
            {minutes ? <Text numberOfLines={1} style={styles.metaText}>{minutes}</Text> : null}
          </View>
          {photo && place.thumbnail?.attribution_text ? <Text numberOfLines={1} style={styles.credit}>{place.thumbnail.attribution_text}</Text> : null}
        </View>
      </View>
    </Pressable>
  );
}

/** "Khám phá {city}": published places of the selected city, filtered by the shared category chip. */
export function ExplorePlaces({ places, state, cityName, filtered, onRetry, onOpenPlace, gutter }: {
  places: Place[];
  state: PlacesLoad;
  cityName: string;
  /** A category chip is active (changes the empty copy). */
  filtered: boolean;
  onRetry: () => void;
  onOpenPlace: (placeId: string) => void;
  gutter: number;
}) {
  const { t } = useTranslation();
  const title = cityName ? t('homeSheet.explore.title', { city: cityName }) : t('homeSheet.explore.titleNoCity');
  const inset = { marginHorizontal: gutter };

  let body;
  if (state === 'loading') {
    body = (
      <View accessibilityLabel={t('homeSheet.explore.loading')} accessibilityRole="progressbar" style={[styles.row, { paddingHorizontal: gutter }]}>
        {[0, 1, 2].map(index => <Skeleton height={CARD_HEIGHT} key={index} radius={radii.card} width={CARD_WIDTH} />)}
      </View>
    );
  } else if (state === 'error') {
    body = <View style={inset}><ErrorBanner message={t('homeSheet.explore.error')} onRetry={onRetry} retryLabel={t('homeSheet.explore.retry')} /></View>;
  } else if (places.length === 0) {
    body = (
      <View style={[styles.empty, inset]}>
        <View style={styles.emptyIcon}><Icon color={colors.tealText} name={filtered ? 'search' : 'map-pin'} size={24} /></View>
        <View style={styles.emptyCopy}>
          {filtered ? (
            <Text style={styles.emptyTitle}>{t('homeSheet.explore.emptyFilter')}</Text>
          ) : (
            <>
              <Text style={styles.emptyTitle}>{t('homeSheet.explore.emptyTitle', { city: cityName })}</Text>
              <Text style={styles.emptyBody}>{t('homeSheet.explore.emptyBody')}</Text>
            </>
          )}
        </View>
      </View>
    );
  } else {
    body = (
      <ScrollView contentContainerStyle={[styles.row, { paddingHorizontal: gutter }]} horizontal showsHorizontalScrollIndicator={false}>
        {places.map(place => <PlaceTile key={place.id} onPress={() => onOpenPlace(place.id)} place={place} />)}
      </ScrollView>
    );
  }

  return (
    <View>
      <SectionHeader style={inset} title={title} />
      {body}
    </View>
  );
}

const styles = StyleSheet.create({
  clip: { backgroundColor: colors.deepOcean, borderRadius: radii.card, height: CARD_HEIGHT, overflow: 'hidden', width: CARD_WIDTH },
  credit: { color: 'rgba(255,255,255,0.82)', fontFamily: fonts.medium, fontSize: 9, marginTop: 4 },
  empty: { alignItems: 'center', backgroundColor: colors.skyWash, borderRadius: radii.card, flexDirection: 'row', gap: spacing.md, padding: spacing.lg },
  emptyBody: { ...typography.caption, marginTop: 2 },
  emptyCopy: { flex: 1 },
  emptyIcon: { alignItems: 'center', backgroundColor: colors.white, borderRadius: 24, height: 48, justifyContent: 'center', width: 48 },
  emptyTitle: { ...typography.label, color: colors.deepOcean },
  meta: { alignItems: 'center', flexDirection: 'row', gap: 5, marginTop: 4 },
  metaText: { color: colors.white, flexShrink: 1, fontFamily: fonts.bold, fontSize: 13 },
  name: { color: colors.white, fontFamily: fonts.bold, fontSize: 16, lineHeight: 20 },
  overlay: { bottom: 0, left: 0, padding: spacing.sm, position: 'absolute', right: 0 },
  pressed: { opacity: 0.9 },
  row: { flexDirection: 'row', gap: spacing.sm, paddingBottom: spacing.sm },
  tile: { backgroundColor: colors.white, borderRadius: radii.card },
});

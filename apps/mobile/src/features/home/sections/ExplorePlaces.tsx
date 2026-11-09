import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { ScrollView } from 'react-native-gesture-handler';

import { CategoryBadge, Icon, Photo, SectionHeader, Skeleton, usePhotoFailed } from '../../../components/ui';
import type { LoadErrorKind } from '../../../lib/api/source';
import type { Category, Place } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { ErrorBanner } from './SheetBanners';

const CARD_WIDTH = 160;
const CARD_HEIGHT = 200;

export type PlacesLoad = 'loading' | 'ready' | 'error';

function PlaceTile({ place, categoryName, onPress }: { place: Place; categoryName: string | null; onPress: () => void }) {
  const { t } = useTranslation();
  const [photoFailed, onPhotoError] = usePhotoFailed(place.thumbnail);
  const minutes = place.visit_minutes_suggested ? t('homeSheet.explore.minutes', { count: place.visit_minutes_suggested }) : null;
  return (
    <Pressable
      accessibilityLabel={[place.name, categoryName, minutes].filter(Boolean).join(', ')}
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.tile, pressed && styles.pressed]}
    >
      <View style={styles.clip}>
        <Photo categoryCode={place.category_code} height={CARD_HEIGHT} image={place.thumbnail} name={place.name} onError={onPhotoError} tone="dark" width={CARD_WIDTH} />
        <LinearGradient colors={['rgba(22,33,43,0)', 'rgba(22,33,43,0.78)']} locations={[0.4, 1]} style={StyleSheet.absoluteFill} />
        {categoryName ? <CategoryBadge code={place.category_code} label={categoryName} style={styles.badge} variant="chip" /> : null}
        <View style={styles.overlay}>
          <Text numberOfLines={2} style={styles.name}>{place.name}</Text>
          {minutes ? <Text numberOfLines={1} style={styles.metaText}>{minutes}</Text> : null}
          {!photoFailed && place.thumbnail?.attribution_text ? <Text numberOfLines={1} style={styles.credit}>{place.thumbnail.attribution_text}</Text> : null}
        </View>
      </View>
    </Pressable>
  );
}

/** "Khám phá {city}": published places of the selected city, filtered (on the server) by the shared category chip. */
export function ExplorePlaces({ places, categories, categoryCode, isVi, state, errorKind, cityName, filtered, onRetry, onOpenPlace, gutter }: {
  places: Place[];
  categories: Category[];
  categoryCode?: string | null;
  isVi: boolean;
  state: PlacesLoad;
  /** Why the last load failed (second line of the retry banner). */
  errorKind?: LoadErrorKind | null;
  cityName: string;
  /** A category chip is active (changes the empty copy). */
  filtered: boolean;
  onRetry: () => void;
  onOpenPlace: (placeId: string) => void;
  gutter: number;
}) {
  const { t } = useTranslation();
  const nameOf = (code: string) => {
    const category = categories.find(item => item.code === code);
    return category ? (isVi ? category.name_vi : category.name_en) : null;
  };
  const categoryTitle = categoryCode ? nameOf(categoryCode) : null;
  const title = categoryTitle || (cityName ? t('homeSheet.explore.title', { city: cityName }) : t('homeSheet.explore.titleNoCity'));
  const inset = { marginHorizontal: gutter };

  let body;
  if (state === 'loading') {
    body = (
      <View accessibilityLabel={t('homeSheet.explore.loading')} accessibilityRole="progressbar" style={[styles.row, { paddingHorizontal: gutter }]}>
        {[0, 1, 2].map(index => <Skeleton height={CARD_HEIGHT} key={index} radius={radii.card} width={CARD_WIDTH} />)}
      </View>
    );
  } else if (state === 'error') {
    body = <View style={inset}><ErrorBanner detail={errorKind ? t(`common.loadError.${errorKind}`) : null} message={t('homeSheet.explore.error')} onRetry={onRetry} retryLabel={t('homeSheet.explore.retry')} /></View>;
  } else if (places.length === 0) {
    body = (
      <View style={[styles.empty, inset]}>
        <View style={styles.emptyIcon}><Icon color={colors.primary} name={filtered ? 'search' : 'map-pin'} size={24} /></View>
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
        {places.map(place => <PlaceTile categoryName={nameOf(place.category_code)} key={place.id} onPress={() => onOpenPlace(place.id)} place={place} />)}
      </ScrollView>
    );
  }

  return (
    <View>
      <SectionHeader
        style={inset}
        subtitle={state === 'ready' && places.length ? t('homeSheet.explore.count', { count: places.length }) : undefined}
        title={title}
      />
      {body}
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { left: spacing.xs, position: 'absolute', top: spacing.xs },
  clip: { backgroundColor: colors.surface, borderRadius: radii.photoCard, height: CARD_HEIGHT, overflow: 'hidden', width: CARD_WIDTH },
  credit: { color: 'rgba(255,255,255,0.82)', fontFamily: fonts.medium, fontSize: 9, marginTop: 4 },
  empty: { alignItems: 'center', backgroundColor: colors.surface, borderRadius: radii.card, flexDirection: 'row', gap: spacing.md, padding: spacing.lg },
  emptyBody: { ...typography.caption, marginTop: 2 },
  emptyCopy: { flex: 1 },
  emptyIcon: { alignItems: 'center', backgroundColor: colors.white, borderRadius: 24, height: 48, justifyContent: 'center', width: 48 },
  emptyTitle: { ...typography.label, color: colors.ink },
  metaText: { color: 'rgba(255,255,255,0.92)', fontFamily: fonts.medium, fontSize: 13, marginTop: 2 },
  name: { color: colors.white, fontFamily: fonts.bold, fontSize: 16, lineHeight: 20 },
  overlay: { bottom: 0, left: 0, padding: spacing.sm, position: 'absolute', right: 0 },
  pressed: { opacity: 0.9 },
  row: { flexDirection: 'row', gap: spacing.sm, paddingBottom: spacing.sm },
  tile: { backgroundColor: colors.white, borderRadius: radii.photoCard },
});

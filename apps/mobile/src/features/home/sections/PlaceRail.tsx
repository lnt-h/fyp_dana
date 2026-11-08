import { useCallback, useEffect, useState } from 'react';
import { Image } from 'expo-image';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { ScrollView } from 'react-native-gesture-handler';

import { Icon, PhotoFallback, SectionHeader, Skeleton, categoryIcon } from '../../../components/ui';
import { searchPlaces } from '../../../lib/api/source';
import type { Category, Place, Uuid } from '../../../lib/api/types';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { ErrorBanner } from './SheetBanners';

const CARD_WIDTH = 196;
const PHOTO_HEIGHT = 124;
const RAIL_MAX = 12;

/**
 * Hội An travel areas (apps/api/data/areas/da-nang.yaml): the Ancient Town side and the beaches/islands side. API-010
 * filters one `area_code` per request, so the rail asks for each and merges.
 */
export const HOI_AN_AREA_CODES = ['hoi-an-old-town', 'hoi-an-beaches-islands'] as const;
const FOOD_CATEGORY_CODES = ['FOOD', 'CAFE'] as const;

type Load = { state: 'loading' } | { state: 'error' } | { state: 'ready'; places: Place[] };

/** Alternates the lists (so cafés and food mix) and drops duplicates, up to `RAIL_MAX`. */
function interleave(lists: Place[][]): Place[] {
  const seen = new Set<Uuid>();
  const out: Place[] = [];
  for (let index = 0; out.length < RAIL_MAX && lists.some(list => index < list.length); index += 1) {
    for (const list of lists) {
      const place = list[index];
      if (place && !seen.has(place.id) && out.length < RAIL_MAX) { seen.add(place.id); out.push(place); }
    }
  }
  return out;
}

function useRail(load: (() => Promise<Place[][]>) | null) {
  const [result, setResult] = useState<Load>({ state: 'loading' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!load) return;
    let active = true;
    setResult({ state: 'loading' });
    load()
      .then(lists => { if (active) setResult({ places: interleave(lists), state: 'ready' }); })
      .catch(() => { if (active) setResult({ state: 'error' }); });
    return () => { active = false; };
  }, [load, attempt]);
  return { result, retry: () => setAttempt(n => n + 1) };
}

function RailCard({ place, categoryName, onPress }: { place: Place; categoryName: string | null; onPress: () => void }) {
  const { t } = useTranslation();
  const photo = resolveImage(place.thumbnail, { height: PHOTO_HEIGHT, width: CARD_WIDTH });
  const minutes = place.visit_minutes_suggested;
  const meta = categoryName && minutes
    ? t('homeSheet.rails.meta', { category: categoryName, count: minutes })
    : minutes ? t('homeSheet.explore.minutes', { count: minutes }) : categoryName;
  return <Pressable
    accessibilityLabel={[place.name, meta].filter(Boolean).join(', ')}
    accessibilityRole="button"
    onPress={onPress}
    style={({ pressed }) => [r.card, pressed && { opacity: 0.88 }]}
  >
    <View style={r.photo}>
      {photo
        ? <Image contentFit="cover" placeholder={photo.placeholder} placeholderContentFit="cover" source={photo.source} style={StyleSheet.absoluteFill} transition={200} />
        : <PhotoFallback icon={categoryIcon(place.category_code)} />}
      {photo && place.thumbnail?.attribution_text
        ? <View style={r.creditWrap}><Text numberOfLines={1} style={r.credit}>{t('homeSheet.rails.credit', { credit: place.thumbnail.attribution_text })}</Text></View>
        : null}
    </View>
    <View style={r.body}>
      <Text numberOfLines={2} style={r.name}>{place.name}</Text>
      {meta ? <View style={r.metaRow}>
        <Icon color={colors.tealText} name={categoryIcon(place.category_code)} size={14} />
        <Text numberOfLines={1} style={r.meta}>{meta}</Text>
      </View> : null}
    </View>
  </Pressable>;
}

/** One themed rail (Vietdetour "Spots in Hội An" pattern): photo or category art, name, `category · about n min`. */
export function PlaceRail({ title, subtitle, load, categories, isVi, onOpenPlace, gutter }: {
  title: string;
  subtitle: string;
  /** Memoised loader; each list is one API-010 page, merged in `interleave`. */
  load: (() => Promise<Place[][]>) | null;
  categories: Category[];
  isVi: boolean;
  onOpenPlace: (placeId: string) => void;
  gutter: number;
}) {
  const { t } = useTranslation();
  const { result, retry } = useRail(load);
  const inset = { marginHorizontal: gutter };
  const nameOf = (code: string) => {
    const category = categories.find(item => item.code === code);
    return category ? (isVi ? category.name_vi : category.name_en) : null;
  };

  let body;
  if (result.state === 'loading') {
    body = <View accessibilityLabel={t('homeSheet.explore.loading')} accessibilityRole="progressbar" style={[r.row, { paddingHorizontal: gutter }]}>
      {[0, 1].map(index => <Skeleton height={PHOTO_HEIGHT + 72} key={index} radius={radii.card} width={CARD_WIDTH} />)}
    </View>;
  } else if (result.state === 'error') {
    body = <View style={inset}><ErrorBanner message={t('homeSheet.explore.error')} onRetry={retry} retryLabel={t('homeSheet.explore.retry')} /></View>;
  } else if (!result.places.length) {
    body = <View style={[r.empty, inset]}>
      <Icon color={colors.tealText} name="map-pin" size={20} />
      <Text style={r.emptyText}>{t('homeSheet.rails.empty')}</Text>
    </View>;
  } else {
    body = <ScrollView contentContainerStyle={[r.row, { paddingHorizontal: gutter }]} horizontal showsHorizontalScrollIndicator={false}>
      {result.places.map(place => <RailCard categoryName={nameOf(place.category_code)} key={place.id} onPress={() => onOpenPlace(place.id)} place={place} />)}
    </ScrollView>;
  }

  return <View>
    <SectionHeader style={inset} subtitle={subtitle} title={title} />
    {body}
  </View>;
}

/** "Spots in Hội An" + "Food & drink" rails for Home (SCR-008), below the category chips. Hội An only for Đà Nẵng. */
export function HomePlaceRails({ cityId, cityCode, categories, isVi, onOpenPlace, gutter }: {
  cityId: Uuid | null;
  cityCode: string | null;
  categories: Category[];
  isVi: boolean;
  onOpenPlace: (placeId: string) => void;
  gutter: number;
}) {
  const { t } = useTranslation();
  const loadHoiAn = useCallback(
    () => Promise.all(HOI_AN_AREA_CODES.map(area => searchPlaces(cityId as Uuid, undefined, null, area))),
    [cityId],
  );
  const loadFood = useCallback(
    () => Promise.all(FOOD_CATEGORY_CODES.map(code => searchPlaces(cityId as Uuid, undefined, code))),
    [cityId],
  );
  if (!cityId) return null;
  return <View style={r.rails}>
    {cityCode === 'da-nang' ? <PlaceRail
      categories={categories}
      gutter={gutter}
      isVi={isVi}
      load={loadHoiAn}
      onOpenPlace={onOpenPlace}
      subtitle={t('homeSheet.rails.hoiAn.subtitle')}
      title={t('homeSheet.rails.hoiAn.title')}
    /> : null}
    <PlaceRail
      categories={categories}
      gutter={gutter}
      isVi={isVi}
      load={loadFood}
      onOpenPlace={onOpenPlace}
      subtitle={t('homeSheet.rails.food.subtitle')}
      title={t('homeSheet.rails.food.title')}
    />
  </View>;
}

const r = StyleSheet.create({
  rails: { gap: spacing.xl },
  row: { flexDirection: 'row', gap: spacing.sm, paddingBottom: spacing.sm },
  card: { width: CARD_WIDTH, borderRadius: radii.card, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.hairline, overflow: 'hidden' },
  photo: { height: PHOTO_HEIGHT, backgroundColor: colors.surfaceTint, justifyContent: 'flex-end' },
  creditWrap: { backgroundColor: 'rgba(7,21,30,0.55)', paddingHorizontal: 6, paddingVertical: 2 },
  credit: { color: colors.white, fontFamily: fonts.medium, fontSize: 9 },
  body: { padding: spacing.sm, gap: 4, minHeight: 72 },
  name: { fontFamily: fonts.bold, fontSize: 15, lineHeight: 20, color: colors.ink },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  meta: { flexShrink: 1, fontFamily: fonts.medium, fontSize: 13, color: colors.textMuted },
  empty: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, padding: spacing.md, borderRadius: radii.card, backgroundColor: colors.surfaceTint },
  emptyText: { ...typography.caption, color: colors.deepOcean, flex: 1 },
});

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { ScrollView } from 'react-native-gesture-handler';

import { Photo, SectionHeader, Skeleton, usePhotoFailed } from '../../../components/ui';
import { loadErrorKind, searchPlaces, type LoadErrorKind } from '../../../lib/api/source';
import type { Category, Place, Uuid } from '../../../lib/api/types';
import { categoryColor, colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { ErrorBanner } from './SheetBanners';

const CARD_WIDTH = 196;
const PHOTO_HEIGHT = 132;
const RAIL_MAX = 12;

/**
 * Hội An travel areas: every area with `hoi_an_area: true` in apps/api/data/areas/da-nang.yaml (keep in sync; the
 * API's `Area` has no Hội An flag). API-010 filters one `area_code` per request, so the rail asks for each and merges.
 */
export const HOI_AN_AREA_CODES = ['hoi-an-old-town', 'hoi-an-beaches-islands', 'hoi-an-outskirts'] as const;
const FOOD_CATEGORY_CODES = ['FOOD', 'CAFE'] as const;
/** Single-category rails after Hội An and food, shown only when the category has published places. */
const CATEGORY_RAILS = ['BEACH', 'VIEWPOINT'] as const;

type Load = { state: 'loading' } | { state: 'error'; kind: LoadErrorKind } | { state: 'ready'; places: Place[] };

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

/** Loads a rail; `load` is memoised on the city, filter and UI language so names follow a language switch. */
function useRail(load: (() => Promise<Place[][]>) | null) {
  const [result, setResult] = useState<Load>({ state: 'loading' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!load) return;
    let active = true;
    setResult({ state: 'loading' });
    load()
      .then(lists => { if (active) setResult({ places: interleave(lists), state: 'ready' }); })
      .catch((error: unknown) => { if (active) setResult({ kind: loadErrorKind(error), state: 'error' }); });
    return () => { active = false; };
  }, [load, attempt]);
  return { result, retry: () => setAttempt(n => n + 1) };
}

/** Photo card: photo (radius 12), name, then a category-colour dot with `category · about n min`. No border. */
function RailCard({ place, categoryName, onPress }: { place: Place; categoryName: string | null; onPress: () => void }) {
  const { t } = useTranslation();
  const [photoFailed, onPhotoError] = usePhotoFailed(place.thumbnail);
  const minutes = place.visit_minutes_suggested;
  const meta = categoryName && minutes
    ? t('homeSheet.rails.meta', { category: categoryName, count: minutes })
    : minutes ? t('homeSheet.explore.minutes', { count: minutes }) : categoryName;
  return <Pressable
    accessibilityLabel={[place.name, meta].filter(Boolean).join(', ')}
    accessibilityRole="button"
    onPress={onPress}
    style={({ pressed }) => [r.card, pressed && r.pressed]}
  >
    <View style={r.photo}>
      <Photo categoryCode={place.category_code} height={PHOTO_HEIGHT} iconSize={40} image={place.thumbnail} name={place.name} onError={onPhotoError} width={CARD_WIDTH} />
      {!photoFailed && place.thumbnail?.attribution_text
        ? <View style={r.creditWrap}><Text numberOfLines={1} style={r.credit}>{t('homeSheet.rails.credit', { credit: place.thumbnail.attribution_text })}</Text></View>
        : null}
    </View>
    <View style={r.body}>
      <Text numberOfLines={2} style={r.name}>{place.name}</Text>
      {meta ? <View style={r.metaRow}>
        <View style={[r.dot, { backgroundColor: categoryColor(place.category_code).fg }]} />
        <Text numberOfLines={1} style={r.meta}>{meta}</Text>
      </View> : null}
    </View>
  </Pressable>;
}

/** One themed rail: photo cards with name and `category · about n min`. Hidden when it has no places. */
export function PlaceRail({ title, subtitle, load, categories, isVi, onOpenPlace, gutter }: {
  title: string;
  subtitle?: string;
  /** Memoised loader; each list is one API-010 query, merged in `interleave`. */
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

  if (result.state === 'ready' && result.places.length === 0) return null;

  let body;
  if (result.state === 'loading') {
    body = <View accessibilityLabel={t('homeSheet.explore.loading')} accessibilityRole="progressbar" style={[r.row, { paddingHorizontal: gutter }]}>
      {[0, 1].map(index => <Skeleton height={PHOTO_HEIGHT + 64} key={index} radius={radii.card} width={CARD_WIDTH} />)}
    </View>;
  } else if (result.state === 'error') {
    body = <View style={inset}><ErrorBanner detail={t(`common.loadError.${result.kind}`)} message={t('homeSheet.explore.error')} onRetry={retry} retryLabel={t('homeSheet.explore.retry')} /></View>;
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

/**
 * Home rails (SCR-008) below the category chips: "Spots in Hội An" (Đà Nẵng only), "Food & drink" and single-category
 * rails, each only when its categories have published places (`populated`, data-driven). Loaders re-run on a city or
 * language change.
 */
export function HomePlaceRails({ cityId, cityCode, categories, populated, isVi, onOpenPlace, gutter }: {
  cityId: Uuid | null;
  cityCode: string | null;
  categories: Category[];
  /** Categories with published places; null while unknown (category rails wait). */
  populated: Category[] | null;
  isVi: boolean;
  onOpenPlace: (placeId: string) => void;
  gutter: number;
}) {
  const { t, i18n } = useTranslation();
  const language = i18n.resolvedLanguage;
  const has = (code: string) => !!populated?.some(category => category.code === code);
  const foodCodes = FOOD_CATEGORY_CODES.filter(has);
  const foodKey = foodCodes.join(',');
  const loadHoiAn = useCallback(
    () => Promise.all(HOI_AN_AREA_CODES.map(area => searchPlaces(cityId as Uuid, undefined, null, area))),
    // `language`: the request locale changes the names returned.
    [cityId, language],
  );
  const loadFood = useCallback(
    () => Promise.all(foodKey.split(',').map(code => searchPlaces(cityId as Uuid, undefined, code))),
    [cityId, foodKey, language],
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
    {foodCodes.length ? <PlaceRail
      categories={categories}
      gutter={gutter}
      isVi={isVi}
      load={loadFood}
      onOpenPlace={onOpenPlace}
      subtitle={t('homeSheet.rails.food.subtitle')}
      title={t('homeSheet.rails.food.title')}
    /> : null}
    {CATEGORY_RAILS.filter(has).map(code => <CategoryRail
      categories={categories}
      cityId={cityId}
      code={code}
      gutter={gutter}
      isVi={isVi}
      key={code}
      language={language}
      onOpenPlace={onOpenPlace}
    />)}
  </View>;
}

function CategoryRail({ code, cityId, language, categories, isVi, onOpenPlace, gutter }: {
  code: string;
  cityId: Uuid;
  language: string | undefined;
  categories: Category[];
  isVi: boolean;
  onOpenPlace: (placeId: string) => void;
  gutter: number;
}) {
  const { t } = useTranslation();
  const load = useCallback(() => searchPlaces(cityId, undefined, code).then(list => [list]), [cityId, code, language]);
  const category = categories.find(item => item.code === code);
  const title = category ? (isVi ? category.name_vi : category.name_en) : code;
  return <PlaceRail
    categories={categories}
    gutter={gutter}
    isVi={isVi}
    load={load}
    onOpenPlace={onOpenPlace}
    subtitle={t(`homeSheet.rails.category.${code === 'BEACH' ? 'BEACH' : 'VIEWPOINT'}`)}
    title={title}
  />;
}

const r = StyleSheet.create({
  rails: { gap: spacing.xl },
  row: { flexDirection: 'row', gap: spacing.md, paddingBottom: spacing.sm },
  card: { width: CARD_WIDTH },
  pressed: { opacity: 0.88, transform: [{ scale: 0.98 }] },
  photo: { height: PHOTO_HEIGHT, borderRadius: radii.photo, overflow: 'hidden', backgroundColor: colors.surface, justifyContent: 'flex-end' },
  creditWrap: { backgroundColor: 'rgba(22,33,43,0.5)', paddingHorizontal: 6, paddingVertical: 2 },
  credit: { color: colors.white, fontFamily: fonts.medium, fontSize: 9 },
  body: { paddingTop: spacing.xs, gap: 2, minHeight: 60 },
  name: { fontFamily: fonts.semibold, fontSize: 15, lineHeight: 20, color: colors.ink },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  meta: { ...typography.micro, flexShrink: 1, color: colors.textSecondary },
});

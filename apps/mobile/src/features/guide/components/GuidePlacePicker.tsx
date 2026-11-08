import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { Icon, Photo, SecondaryButton, SectionHeader, Skeleton } from '../../../components/ui';
import { currentLocale } from '../../../i18n';
import { listCategories, listCities } from '../../../lib/api/source';
import { DEFAULT_CITY_CODE, type Category, type City, type Place } from '../../../lib/api/types';
import { categoryColor, colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { searchPlacesPage } from '../guideApi';

type Load =
  | { state: 'loading' }
  | { state: 'ready'; places: Place[]; next: string | null; more: boolean }
  | { state: 'error' };

const THUMB = 64;
const SEARCH_DEBOUNCE_MS = 300;

/**
 * Place picker: a "whole city" entry (city session), then the city's places with search (`q`) and cursor paging
 * (API-010), so every published place is reachable, not just the first page.
 */
export function GuidePlacePicker({ onPick, onPickCity }: { onPick: (placeId: string) => void; onPickCity?: () => void }) {
  const { t, i18n } = useTranslation();
  const [city, setCity] = useState<City | null>(null);
  const [load, setLoad] = useState<Load>({ state: 'loading' });
  const [categories, setCategories] = useState<Category[]>([]);
  const [query, setQuery] = useState('');
  const [debounced, setDebounced] = useState('');
  const [attempt, setAttempt] = useState(0);
  const request = useRef(0);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(query.trim()), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    listCategories().then(setCategories).catch(() => undefined);
  }, [i18n.language]);

  useEffect(() => {
    const id = ++request.current;
    setLoad({ state: 'loading' });
    (async () => {
      const found = city ?? (await listCities()).find(item => item.code === DEFAULT_CITY_CODE) ?? null;
      if (!found) return { found, next: null, places: [] as Place[] };
      const page = await searchPlacesPage(found.id, currentLocale(), debounced, null);
      return { found, next: page.next, places: page.items };
    })()
      .then(({ found, places, next }) => {
        if (id !== request.current) return;
        setCity(found);
        setLoad({ more: false, next, places, state: 'ready' });
      })
      .catch(() => { if (id === request.current) setLoad({ state: 'error' }); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attempt, debounced, i18n.language]);

  function loadMore() {
    if (load.state !== 'ready' || !load.next || load.more || !city) return;
    const id = request.current;
    const current = load;
    setLoad({ ...current, more: true });
    searchPlacesPage(city.id, currentLocale(), debounced, current.next)
      .then(page => { if (id === request.current) setLoad({ more: false, next: page.next, places: [...current.places, ...page.items], state: 'ready' }); })
      .catch(() => { if (id === request.current) setLoad({ ...current, more: false }); });
  }

  const locale = currentLocale();
  const cityName = city ? (locale === 'vi' ? city.name_vi : city.name_en) : '';

  return <View>
    {onPickCity && <Pressable
      accessibilityLabel={`${t('guide.picker.wholeCity', { city: cityName })}. ${t('guide.picker.wholeCityBody')}`}
      accessibilityRole="button"
      onPress={onPickCity}
      style={({ pressed }) => [p.cityRow, pressed && p.pressed]}
    >
      <View style={p.cityIcon}><Icon color={colors.white} name="map-pin" size={24} /></View>
      <View style={p.copy}>
        <Text numberOfLines={2} style={p.cityName}>{t('guide.picker.wholeCity', { city: cityName })}</Text>
        <Text numberOfLines={2} style={p.cityBody}>{t('guide.picker.wholeCityBody')}</Text>
      </View>
      <Icon color={colors.primary} name="chevron-right" size={20} />
    </Pressable>}

    <SectionHeader style={p.section} title={t('guide.picker.choose')} />

    <View style={p.search}>
      <Icon color={colors.textMuted} name="search" size={18} />
      <TextInput
        accessibilityLabel={t('guide.picker.searchLabel')}
        autoCorrect={false}
        clearButtonMode="never"
        onChangeText={setQuery}
        placeholder={t('guide.picker.searchPlaceholder')}
        placeholderTextColor={colors.textMuted}
        returnKeyType="search"
        style={p.searchInput}
        value={query}
      />
      {!!query && <Pressable accessibilityLabel={t('guide.picker.clearSearch')} accessibilityRole="button" hitSlop={10} onPress={() => setQuery('')} style={p.clear}>
        <Icon color={colors.textSecondary} name="close" size={16} />
      </Pressable>}
    </View>

    {load.state === 'loading' && <View accessibilityLabel={t('guide.picker.loading')} accessibilityLiveRegion="polite" accessible style={p.list}>
      {[0, 1, 2, 3].map(key => <View key={key} style={p.skeletonRow}>
        <Skeleton height={THUMB} radius={radii.photo} width={THUMB} />
        <View style={p.copy}>
          <Skeleton height={18} width="70%" />
          <Skeleton height={14} width="45%" />
        </View>
      </View>)}
    </View>}

    {load.state === 'error' && <View style={p.status}>
      <Icon color={colors.textMuted} name="warning" size={28} />
      <Text accessibilityRole="alert" style={p.statusText}>{t('guide.picker.error')}</Text>
      <SecondaryButton label={t('guide.picker.retry')} onPress={() => setAttempt(n => n + 1)} />
    </View>}

    {load.state === 'ready' && (load.places.length === 0
      ? <View style={p.status}>
        <Icon color={colors.textMuted} name="search" size={28} />
        <Text accessibilityLiveRegion="polite" style={p.statusText}>{debounced ? t('guide.picker.noResults', { q: debounced }) : t('guide.picker.empty')}</Text>
        {!!debounced && <SecondaryButton label={t('guide.picker.clearSearch')} onPress={() => setQuery('')} />}
      </View>
      : <View style={p.list}>
        {load.places.map(place => <PlaceRow
          category={categories.find(item => item.code === place.category_code)}
          key={place.id}
          onPress={() => onPick(place.id)}
          place={place}
        />)}
        {load.next && <Pressable accessibilityRole="button" accessibilityState={{ busy: load.more }} disabled={load.more} onPress={loadMore} style={({ pressed }) => [p.more, pressed && p.pressed]}>
          {load.more ? <ActivityIndicator color={colors.primary} /> : <Text style={p.moreText}>{t('guide.picker.loadMore')}</Text>}
        </Pressable>}
      </View>)}
  </View>;
}

function PlaceRow({ place, category, onPress }: { place: Place; category?: Category; onPress: () => void }) {
  const { t } = useTranslation();
  const locale = currentLocale();
  const categoryName = category ? (locale === 'vi' ? category.name_vi : category.name_en) : null;
  const tone = categoryColor(place.category_code);
  return <Pressable
    accessibilityHint={t('guide.picker.a11yPlace', { name: place.name })}
    accessibilityLabel={[place.name, categoryName].filter(Boolean).join(', ')}
    accessibilityRole="button"
    onPress={onPress}
    style={({ pressed }) => [p.row, pressed && p.pressed]}
  >
    <View style={p.thumb}>
      <Photo categoryCode={place.category_code} height={THUMB} iconSize={24} image={place.thumbnail} name={place.name} variant="thumb" width={THUMB} />
    </View>
    <View style={p.copy}>
      <Text numberOfLines={2} style={p.name}>{place.name}</Text>
      {!!categoryName && <View style={p.metaRow}>
        <View style={[p.dot, { backgroundColor: tone.fg }]} />
        <Text numberOfLines={1} style={p.meta}>{categoryName}</Text>
      </View>}
    </View>
    <Icon color={colors.textMuted} name="chevron-right" size={18} />
  </Pressable>;
}

const p = StyleSheet.create({
  cityBody: { ...typography.caption, color: colors.textSecondary, fontSize: 14, lineHeight: 19 },
  cityIcon: { alignItems: 'center', backgroundColor: colors.primary, borderRadius: radii.iconTile, height: 48, justifyContent: 'center', width: 48 },
  cityName: { ...typography.bodyStrong },
  cityRow: { alignItems: 'center', backgroundColor: colors.primarySoft, borderRadius: radii.card, flexDirection: 'row', gap: 14, marginTop: spacing.xs, padding: spacing.md },
  clear: { alignItems: 'center', backgroundColor: colors.hairline, borderRadius: 12, height: 24, justifyContent: 'center', width: 24 },
  copy: { flex: 1, gap: 4, minWidth: 0 },
  dot: { borderRadius: 4, height: 8, width: 8 },
  list: { gap: 2 },
  meta: { ...typography.caption, color: colors.textSecondary, flexShrink: 1 },
  metaRow: { alignItems: 'center', flexDirection: 'row', gap: 6 },
  more: { alignItems: 'center', backgroundColor: colors.surface, borderRadius: radii.button, justifyContent: 'center', marginTop: spacing.sm, minHeight: MIN_TOUCH + 4 },
  moreText: { color: colors.primary, fontFamily: fonts.semibold, fontSize: 15 },
  name: { ...typography.bodyStrong, lineHeight: 21 },
  pressed: { opacity: 0.75 },
  row: { alignItems: 'center', borderRadius: radii.card, flexDirection: 'row', gap: 14, minHeight: MIN_TOUCH, paddingVertical: 8 },
  search: { alignItems: 'center', backgroundColor: colors.surface, borderRadius: radii.pill, flexDirection: 'row', gap: 8, marginBottom: spacing.sm, minHeight: 48, paddingHorizontal: 16 },
  searchInput: { color: colors.ink, flex: 1, fontFamily: fonts.regular, fontSize: 16, minHeight: 44 },
  section: { marginBottom: spacing.sm, marginTop: spacing.xl },
  skeletonRow: { alignItems: 'center', flexDirection: 'row', gap: 14, paddingVertical: 8 },
  status: { alignItems: 'center', gap: 12, paddingVertical: 28 },
  statusText: { ...typography.body, color: colors.textSecondary, textAlign: 'center' },
  thumb: { backgroundColor: colors.surface, borderRadius: radii.photo, height: THUMB, overflow: 'hidden', width: THUMB },
});

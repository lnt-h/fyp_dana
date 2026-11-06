import { useEffect, useState } from 'react';
import { Image } from 'expo-image';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon, SecondaryButton, SectionHeader, Skeleton, categoryIcon, PhotoFallback } from '../../../components/ui';
import { currentLocale } from '../../../i18n';
import { listCategories, listCities, searchPlaces } from '../../../lib/api/source';
import { DEFAULT_CITY_CODE, type Category, type City, type Place } from '../../../lib/api/types';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { washMuted } from './GuideHeader';

type Load = { state: 'loading' } | { state: 'ready'; places: Place[]; city: City | null } | { state: 'error' };

const THUMB = 76;

/** Place picker: explainer, a "whole city" entry (city session) and the city's places (place session). */
export function GuidePlacePicker({ onPick, onPickCity }: { onPick: (placeId: string) => void; onPickCity?: () => void }) {
  const { t, i18n } = useTranslation();
  const [load, setLoad] = useState<Load>({ state: 'loading' });
  const [categories, setCategories] = useState<Category[]>([]);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoad({ state: 'loading' });
    (async () => {
      const city = (await listCities()).find(item => item.code === DEFAULT_CITY_CODE) ?? null;
      return { city, places: city ? await searchPlaces(city.id) : [] };
    })()
      .then(({ city, places }) => { if (alive) setLoad({ city, places, state: 'ready' }); })
      .catch(() => { if (alive) setLoad({ state: 'error' }); });
    listCategories().then(items => { if (alive) setCategories(items); }).catch(() => undefined);
    return () => { alive = false; };
  }, [attempt, i18n.language]);

  const locale = currentLocale();
  const cityName = load.state === 'ready' && load.city ? (locale === 'vi' ? load.city.name_vi : load.city.name_en) : undefined;

  return <View>
    <View style={p.intro}>
      <View style={p.introIcon}><Icon color={colors.tealText} name="check" size={20} /></View>
      <View style={p.introCopy}>
        <Text style={p.introTitle}>{t('guide.picker.title')}</Text>
        <Text style={p.introBody}>{t('guide.picker.body')}</Text>
      </View>
    </View>

    {onPickCity && <Pressable
      accessibilityLabel={t('guide.picker.wholeCity', { city: cityName ?? '' })}
      accessibilityRole="button"
      onPress={onPickCity}
      style={({ pressed }) => [p.row, p.cityRow, pressed && p.pressed]}
    >
      <View style={[p.thumb, p.cityThumb]}><Icon color={colors.tealText} name="map-pin" size={28} /></View>
      <View style={p.copy}>
        <Text numberOfLines={1} style={p.name}>{t('guide.picker.wholeCity', { city: cityName ?? '' })}</Text>
        <Text numberOfLines={2} style={p.description}>{t('guide.picker.wholeCityBody')}</Text>
      </View>
      <View style={p.chevron}><Icon color={colors.deepOcean} name="chevron-right" size={18} /></View>
    </Pressable>}

    <SectionHeader style={p.section} subtitle={cityName} title={t('guide.picker.choose')} />

    {load.state === 'loading' && <View accessibilityLabel={t('guide.picker.loading')} accessibilityLiveRegion="polite" accessible style={p.list}>
      {[0, 1, 2, 3].map(key => <View key={key} style={p.skeletonRow}>
        <Skeleton height={THUMB} radius={radii.inset} width={THUMB} />
        <View style={p.copy}>
          <Skeleton height={18} width="70%" />
          <Skeleton height={14} width="90%" />
        </View>
      </View>)}
    </View>}

    {load.state === 'error' && <View style={p.status}>
      <Text accessibilityRole="alert" style={p.statusText}>{t('guide.picker.error')}</Text>
      <SecondaryButton label={t('guide.picker.retry')} onPress={() => setAttempt(n => n + 1)} />
    </View>}

    {load.state === 'ready' && (load.places.length === 0
      ? <Text style={p.statusText}>{t('guide.picker.empty')}</Text>
      : <View style={p.list}>
        {load.places.map(place => <PlaceRow
          category={categories.find(item => item.code === place.category_code)}
          key={place.id}
          onPress={() => onPick(place.id)}
          place={place}
        />)}
      </View>)}
  </View>;
}

function PlaceRow({ place, category, onPress }: { place: Place; category?: Category; onPress: () => void }) {
  const { t } = useTranslation();
  const locale = currentLocale();
  const resolved = resolveImage(place.thumbnail, { height: THUMB, width: THUMB });
  const categoryName = category ? (locale === 'vi' ? category.name_vi : category.name_en) : null;
  const meta = [categoryName, place.visit_minutes_suggested ? t('guide.picker.minutes', { count: place.visit_minutes_suggested }) : null].filter(Boolean).join(' · ');
  return <Pressable
    accessibilityHint={t('guide.picker.a11yPlace', { name: place.name })}
    accessibilityLabel={[place.name, place.short_description, meta].filter(Boolean).join('. ')}
    accessibilityRole="button"
    onPress={onPress}
    style={({ pressed }) => [p.row, pressed && p.pressed]}
  >
    <View style={p.thumb}>
      {resolved
        ? <Image contentFit="cover" placeholder={resolved.placeholder} source={resolved.source} style={StyleSheet.absoluteFill} transition={200} />
        : <PhotoFallback icon={categoryIcon(place.category_code)} iconSize={28} />}
    </View>
    <View style={p.copy}>
      <Text numberOfLines={1} style={p.name}>{place.name}</Text>
      {!!place.short_description && <Text numberOfLines={1} style={p.description}>{place.short_description}</Text>}
      {!!meta && <View style={p.metaRow}>
        <Icon color={colors.tealText} name={categoryIcon(place.category_code)} size={15} />
        <Text numberOfLines={1} style={p.meta}>{meta}</Text>
      </View>}
    </View>
    <View style={p.chevron}><Icon color={colors.deepOcean} name="chevron-right" size={18} /></View>
  </Pressable>;
}

const p = StyleSheet.create({
  cityRow: { marginTop: spacing.md },
  cityThumb: { alignItems: 'center', justifyContent: 'center' },
  chevron: { alignItems: 'center', backgroundColor: colors.surfaceTint, borderRadius: 16, height: 32, justifyContent: 'center', width: 32 },
  copy: { flex: 1, gap: 4, minWidth: 0 },
  description: { color: colors.textMuted, fontFamily: fonts.regular, fontSize: 14, lineHeight: 19 },
  intro: { alignItems: 'flex-start', backgroundColor: colors.surfaceTint, borderRadius: radii.card, flexDirection: 'row', gap: 12, marginTop: spacing.xs, padding: spacing.md },
  introBody: { color: washMuted, fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, marginTop: 2 },
  introCopy: { flex: 1 },
  introIcon: { alignItems: 'center', backgroundColor: colors.white, borderRadius: 18, height: 36, justifyContent: 'center', width: 36 },
  introTitle: { color: colors.ink, fontFamily: fonts.bold, fontSize: 16, lineHeight: 22 },
  list: { gap: spacing.sm },
  meta: { color: colors.tealText, flexShrink: 1, fontFamily: fonts.bold, fontSize: 13, lineHeight: 17 },
  metaRow: { alignItems: 'center', flexDirection: 'row', gap: 5 },
  name: { color: colors.ink, fontFamily: fonts.bold, fontSize: 17, lineHeight: 22 },
  pressed: { opacity: 0.9, transform: [{ scale: 0.99 }] },
  row: { alignItems: 'center', backgroundColor: colors.white, borderColor: colors.hairline, borderRadius: radii.card, borderWidth: 1, flexDirection: 'row', gap: 14, padding: 10, paddingRight: 14 },
  section: { marginBottom: spacing.sm, marginTop: spacing.xl },
  skeletonRow: { alignItems: 'center', flexDirection: 'row', gap: 14, padding: 10 },
  status: { alignItems: 'stretch', gap: 12, paddingVertical: 24 },
  statusText: { color: colors.textMuted, fontFamily: fonts.regular, fontSize: 15, lineHeight: 22, textAlign: 'center' },
  thumb: { backgroundColor: colors.surfaceTint, borderRadius: radii.inset, height: THUMB, overflow: 'hidden', width: THUMB },
});

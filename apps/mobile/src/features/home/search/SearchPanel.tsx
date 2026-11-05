import { BottomSheetTextInput } from '@gorhom/bottom-sheet';
import { Image } from 'expo-image';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Chip, Icon, SecondaryButton, Skeleton, categoryIcon } from '../../../components/ui';
import { listCategories, searchPlaces } from '../../../lib/api/source';
import type { Category, City, Place } from '../../../lib/api/types';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { fonts } from '../../../theme/typography';

const DEBOUNCE_MS = 300;
const MAX_QUERY = 120;
const MAX_RESULTS = 20;

type Status = 'idle' | 'loading' | 'done' | 'error';

type HeaderProps = {
  query: string;
  onChangeQuery: (q: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
  cityName: string;
  offline: boolean;
};

/** Sticky search field of SCR-021 (autofocus, clear 44 pt, Cancel). */
export function SearchHeader({ query, onChangeQuery, onSubmit, onCancel, cityName, offline }: HeaderProps) {
  const { t } = useTranslation();
  return (
    <View style={styles.header}>
      <View style={styles.field}>
        <Icon color={colors.textMuted} name="search" size={20} />
        <BottomSheetTextInput
          accessibilityLabel={t('home.search.pillLabel', { city: cityName })}
          autoCorrect={false}
          autoFocus={!offline}
          editable={!offline}
          maxLength={MAX_QUERY}
          onChangeText={onChangeQuery}
          onSubmitEditing={onSubmit}
          placeholder={t('home.search.placeholder', { city: cityName })}
          placeholderTextColor={colors.textMuted}
          returnKeyType="search"
          style={styles.input}
          value={query}
        />
        {query ? (
          <Pressable accessibilityLabel={t('home.search.clear')} accessibilityRole="button" onPress={() => onChangeQuery('')} style={styles.clear}>
            <View style={styles.clearDot}>
              <Text style={styles.clearGlyph}>×</Text>
            </View>
          </Pressable>
        ) : null}
      </View>
      <Pressable accessibilityRole="button" hitSlop={6} onPress={onCancel} style={styles.cancel}>
        <Text style={styles.cancelText}>{t('home.search.cancel')}</Text>
      </Pressable>
    </View>
  );
}

type BodyProps = {
  city: City;
  query: string;
  offline: boolean;
  recent: string[];
  onPickRecent: (q: string) => void;
  onOpenPlace: (place: Place) => void;
  onChangeCity: () => void;
};

/** SCR-021 body: idle (recent searches + topics), loading, results, empty, error and offline states. */
export function SearchBody({ city, query, offline, recent, onPickRecent, onOpenPlace, onChangeCity }: BodyProps) {
  const { t, i18n } = useTranslation();
  const vi = i18n.resolvedLanguage === 'vi';
  const cityName = vi ? city.name_vi : city.name_en;
  const [categories, setCategories] = useState<Category[]>([]);
  const [topic, setTopic] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [items, setItems] = useState<Place[]>([]);
  const [attempt, setAttempt] = useState(0);
  const q = query.trim();

  useEffect(() => {
    let active = true;
    listCategories().then(list => { if (active) setCategories([...list].sort((a, b) => a.sort_order - b.sort_order)); }).catch(() => undefined);
    return () => { active = false; };
  }, []);

  // Typing replaces a topic shortcut.
  useEffect(() => { if (q) setTopic(null); }, [q]);

  useEffect(() => {
    if (offline || (!q && !topic)) { setStatus('idle'); return; }
    let active = true;
    setStatus('loading'); // previous results stay visible while loading
    const timer = setTimeout(() => {
      searchPlaces(city.id, q || undefined)
        .then(found => {
          if (!active) return;
          setItems((topic ? found.filter(place => place.category_code === topic) : found).slice(0, MAX_RESULTS));
          setStatus('done');
        })
        .catch(() => { if (active) setStatus('error'); });
    }, q ? DEBOUNCE_MS : 0);
    return () => { active = false; clearTimeout(timer); };
  }, [attempt, city.id, offline, q, topic]);

  const categoryName = useMemo(() => {
    const map = new Map(categories.map(c => [c.code, vi ? c.name_vi : c.name_en]));
    return (code: string) => map.get(code) ?? '';
  }, [categories, vi]);

  if (offline) {
    return (
      <View accessibilityLiveRegion="polite" style={styles.banner}>
        <Icon color={colors.ink} name="info" size={20} />
        <Text style={styles.bannerText}>{t('home.search.offlineHint')}</Text>
      </View>
    );
  }

  if (status === 'idle') {
    return (
      <View style={styles.idle}>
        {recent.length > 0 ? (
          <View style={styles.group}>
            <Text accessibilityRole="header" style={styles.caption}>{t('home.search.recent')}</Text>
            {recent.map(item => (
              <Pressable accessibilityRole="button" key={item} onPress={() => onPickRecent(item)} style={styles.recentRow}>
                <Icon color={colors.textMuted} name="clock" size={18} />
                <Text numberOfLines={1} style={styles.recentText}>{item}</Text>
              </Pressable>
            ))}
          </View>
        ) : null}
        {categories.length > 0 ? (
          <View style={styles.group}>
            <Text accessibilityRole="header" style={styles.caption}>{t('home.search.topics')}</Text>
            <View style={styles.chips}>
              {categories.map(category => (
                <Chip
                  icon={categoryIcon(category.code)}
                  key={category.code}
                  label={vi ? category.name_vi : category.name_en}
                  onPress={() => setTopic(category.code)}
                  tone="tint"
                />
              ))}
            </View>
          </View>
        ) : null}
      </View>
    );
  }

  if (status === 'error') {
    return (
      <View accessibilityLiveRegion="polite" style={styles.banner}>
        <Icon color={colors.ink} name="warning" size={20} />
        <Text style={styles.bannerText}>{t('home.search.error')}</Text>
        <Pressable accessibilityRole="button" hitSlop={8} onPress={() => setAttempt(n => n + 1)}>
          <Text style={styles.link}>{t('home.search.retry')}</Text>
        </Pressable>
      </View>
    );
  }

  const loading = status === 'loading';
  const showSkeleton = loading && items.length === 0;

  if (!loading && items.length === 0) {
    return (
      <View style={styles.empty}>
        <View style={styles.emptyGlyph}>
          <Icon color={colors.tealText} name="search" size={26} />
        </View>
        <Text accessibilityLiveRegion="polite" style={styles.emptyTitle}>
          {q ? t('home.search.emptyTitle', { city: cityName, q }) : t('home.search.emptyTopicTitle', { city: cityName })}
        </Text>
        <Text style={styles.emptyBody}>{t('home.search.emptyBody')}</Text>
        <SecondaryButton label={t('home.search.changeCity')} onPress={onChangeCity} />
      </View>
    );
  }

  return (
    <View>
      <Text accessibilityLiveRegion="polite" accessibilityRole="text" style={styles.status}>
        {loading ? t('home.search.searching') : t('home.search.resultCount', { city: cityName, count: items.length })}
      </Text>
      {topic ? (
        <View style={styles.topicRow}>
          <Chip icon={categoryIcon(topic)} label={categoryName(topic)} onPress={() => setTopic(null)} selected />
        </View>
      ) : null}
      {showSkeleton
        ? Array.from({ length: 3 }, (_, i) => (
          <View key={i} style={styles.row}>
            <Skeleton height={56} radius={14} width={56} />
            <View style={styles.rowBody}>
              <Skeleton height={16} width="70%" />
              <Skeleton height={12} width="45%" />
            </View>
          </View>
        ))
        : items.map(place => (
          <ResultRow categoryLabel={categoryName(place.category_code)} key={place.id} onPress={() => onOpenPlace(place)} place={place} />
        ))}
    </View>
  );
}

function ResultRow({ place, categoryLabel, onPress }: { place: Place; categoryLabel: string; onPress: () => void }) {
  const image = resolveImage(place.thumbnail, { height: 56, width: 56 });
  // `name` is in the UI language; `name_vi` is always present, so it is the other-language name only in English.
  const secondary = place.name_vi !== place.name ? place.name_vi : null;
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [styles.row, pressed && styles.pressed]}>
      <View style={styles.thumb}>
        {image ? (
          <Image contentFit="cover" placeholder={image.placeholder} source={image.source} style={StyleSheet.absoluteFill} />
        ) : (
          <Icon color={colors.tealText} name={categoryIcon(place.category_code)} size={24} />
        )}
      </View>
      <View style={styles.rowBody}>
        <Text numberOfLines={1} style={styles.rowName}>{place.name}</Text>
        {secondary ? <Text numberOfLines={1} style={styles.rowSecondary}>{secondary}</Text> : null}
        <View style={styles.rowMeta}>
          <Icon color={colors.tealText} name={categoryIcon(place.category_code)} size={16} />
          {categoryLabel ? <Text numberOfLines={1} style={styles.rowMetaText}>{categoryLabel}</Text> : null}
        </View>
      </View>
      <Icon color={colors.ink} name="chevron-right" size={20} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  banner: {
    alignItems: 'center',
    backgroundColor: colors.skyWash,
    borderRadius: 16,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginTop: 8,
    padding: 14,
  },
  bannerText: { color: colors.ink, flex: 1, fontFamily: fonts.medium, fontSize: 15, lineHeight: 22, minWidth: 180 },
  cancel: { justifyContent: 'center', minHeight: 44, paddingLeft: 4 },
  cancelText: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 16, lineHeight: 22 },
  caption: { color: colors.textMuted, fontFamily: fonts.bold, fontSize: 13, letterSpacing: 0.4, lineHeight: 18, textTransform: 'uppercase' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  clear: { alignItems: 'center', height: 44, justifyContent: 'center', width: 44 },
  clearDot: { alignItems: 'center', backgroundColor: colors.textMuted, borderRadius: 10, height: 20, justifyContent: 'center', width: 20 },
  clearGlyph: { color: colors.white, fontFamily: fonts.bold, fontSize: 15, lineHeight: 18 },
  empty: { alignItems: 'center', backgroundColor: colors.skyWash, borderRadius: 24, gap: 10, marginTop: 8, padding: 20 },
  emptyBody: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 15, lineHeight: 22, textAlign: 'center' },
  emptyGlyph: { alignItems: 'center', backgroundColor: colors.white, borderRadius: 24, height: 48, justifyContent: 'center', width: 48 },
  emptyTitle: { color: colors.ink, fontFamily: fonts.bold, fontSize: 17, lineHeight: 24, textAlign: 'center' },
  field: {
    alignItems: 'center',
    backgroundColor: colors.white,
    borderColor: '#A9D6DE',
    borderRadius: 26,
    borderWidth: 1,
    flex: 1,
    flexDirection: 'row',
    height: 52,
    paddingLeft: 16,
  },
  group: { gap: 10 },
  header: { alignItems: 'center', backgroundColor: colors.white, flexDirection: 'row', gap: 8, paddingBottom: 12, paddingTop: 4 },
  idle: { gap: 22, paddingTop: 8 },
  input: { color: colors.ink, flex: 1, fontFamily: fonts.medium, fontSize: 16, height: '100%', marginLeft: 10, paddingVertical: 0 },
  link: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 15, lineHeight: 22, textDecorationLine: 'underline' },
  pressed: { opacity: 0.8 },
  recentRow: { alignItems: 'center', flexDirection: 'row', gap: 10, minHeight: 44 },
  recentText: { color: colors.ink, flex: 1, fontFamily: fonts.medium, fontSize: 16, lineHeight: 22 },
  row: { alignItems: 'center', flexDirection: 'row', gap: 12, minHeight: 72, paddingVertical: 8 },
  rowBody: { flex: 1, gap: 4 },
  rowMeta: { alignItems: 'center', flexDirection: 'row', gap: 6 },
  rowMetaText: { color: colors.textMuted, flexShrink: 1, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18 },
  rowName: { color: colors.ink, fontFamily: fonts.bold, fontSize: 16, lineHeight: 22 },
  rowSecondary: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 14, lineHeight: 20 },
  status: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 14, lineHeight: 20, marginBottom: 4 },
  thumb: { alignItems: 'center', backgroundColor: colors.skyWash, borderRadius: 14, height: 56, justifyContent: 'center', overflow: 'hidden', width: 56 },
  topicRow: { alignItems: 'flex-start', marginBottom: 4 },
});

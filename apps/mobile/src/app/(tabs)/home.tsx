import BottomSheet, { BottomSheetScrollView } from '@gorhom/bottom-sheet';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Keyboard, Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import type MapView from 'react-native-maps';
import Animated, { ReduceMotion, useAnimatedStyle, useSharedValue } from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Wordmark } from '../../components/brand/BrandMarks';
import { CircleButton, Icon } from '../../components/ui';
import { useAccount } from '../../features/account/AccountContext';
import { AccountIcon } from '../../features/account/AccountUI';
import { SignInGate, type GateFeature } from '../../features/auth/SignInGate';
import { CityButton } from '../../features/home/city/CityButton';
import { CitySheet } from '../../features/home/city/CitySheet';
import { useSelectedCity } from '../../features/home/cityStore';
import { useTabBarHeight } from '../../features/home/components/HomeTabBar';
import { HomeMap } from '../../features/home/map/HomeMap';
import { PlacePreviewCard } from '../../features/home/map/PlacePreviewCard';
import { cityRegion, framedRegion } from '../../features/home/map/region';
import { useLocateMe } from '../../features/home/map/useLocateMe';
import { SearchBody, SearchHeader } from '../../features/home/search/SearchPanel';
import { SearchPill } from '../../features/home/search/SearchPill';
import { HomeSheetContent } from '../../features/home/sections/HomeSheetContent';
import { useIsOffline } from '../../features/home/useNetwork';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { searchPlaces } from '../../lib/api/source';
import type { Place } from '../../lib/api/types';
import { colors } from '../../theme/colors';
import { elevation } from '../../theme/elevation';
import { radii, spacing } from '../../theme/spacing';
import { fonts } from '../../theme/typography';

/** COLLAPSED is measured from the screen bottom (the sheet runs under the floating tab bar), so it is 26% rather than 22%
 *  to keep the handle and the greeting visible above the pill. */
const SNAP_POINTS = ['26%', '52%', '92%'];
/** Fraction of the screen the sheet covers at HALF (initial map padding before the first snap reports its position). */
const HALF_FRACTION = 0.52;
const HALF = 1;
const FULL = 2;
const MAX_MARKERS = 20;
const MAX_RECENT = 5;
const GUTTER = 20;

type CityPlaces = { cityId: string; items: Place[] };

export default function HomeScreen() {
  const { t, i18n } = useTranslation();
  const insets = useSafeAreaInsets();
  const { height, width } = useWindowDimensions();
  const aspect = width / height;
  const reduced = useReducedMotion();
  const offline = useIsOffline();
  const tabBarHeight = useTabBarHeight();
  const { isSignedIn, profile } = useAccount();
  const { city } = useSelectedCity();
  const cityName = city ? (i18n.resolvedLanguage === 'vi' ? city.name_vi : city.name_en) : null;

  const mapRef = useRef<MapView>(null);
  const sheetRef = useRef<BottomSheet>(null);
  const sheetTop = useSharedValue(height);
  const [sheetIndex, setSheetIndex] = useState(HALF);
  const [initialRegion] = useState(() => cityRegion(city?.code, [], aspect));
  // Map padding follows the sheet's resting height (not FULL, where the map is hidden) so Legal stays above the sheet.
  const [mapBottom, setMapBottom] = useState(() => Math.round(height * HALF_FRACTION));

  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [cityPlaces, setCityPlaces] = useState<CityPlaces | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [citySheetOpen, setCitySheetOpen] = useState(false);
  const [gate, setGate] = useState<GateFeature | null>(null);
  const [searching, setSearching] = useState(false);
  const [query, setQuery] = useState('');
  /** Recent queries for this session only: memory, never stored or logged. */
  const [recent, setRecent] = useState<string[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const { granted, locate } = useLocateMe();

  // Markers: published places of the selected city (API-010, no q).
  useEffect(() => {
    if (!city) return;
    let active = true;
    setSelectedId(null);
    searchPlaces(city.id)
      .then(items => { if (active) setCityPlaces({ cityId: city.id, items }); })
      .catch(() => { if (active) setCityPlaces({ cityId: city.id, items: [] }); });
    return () => { active = false; };
  }, [city]);

  const places = useMemo(() => (cityPlaces && cityPlaces.cityId === city?.id ? cityPlaces.items : []), [city?.id, cityPlaces]);
  const markers = useMemo(
    () => (categoryFilter ? places.filter(place => place.category_code === categoryFilter) : places).slice(0, MAX_MARKERS),
    [categoryFilter, places],
  );
  const selectedPlace = markers.find(place => place.id === selectedId) ?? null;

  // Re-centre once the city's places are known (fallback centre when it has none yet).
  const loadedFor = cityPlaces?.cityId === city?.id ? city?.id : undefined;
  useEffect(() => {
    if (!city || !loadedFor) return;
    const points = places.map(place => place.location);
    if (points.length > 1) {
      // Centre on the median place (the dense core, e.g. Hội An old town) at street zoom so markers do not pile up;
      // outlying places stay one pan away.
      const median = (values: number[]) => [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)];
      const core = { latitude: median(points.map(p => p.latitude)), longitude: median(points.map(p => p.longitude)) };
      mapRef.current?.animateToRegion(framedRegion(core, 0.018, aspect), reduced ? 0 : 600);
    } else {
      mapRef.current?.animateToRegion(cityRegion(city.code, points, aspect), reduced ? 0 : 600);
    }
    // Runs once per loaded city, not on resize or motion-setting changes.
  }, [loadedFor]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(timer);
  }, [toast]);

  const openPlace = useCallback((placeId: string) => {
    router.push({ params: { placeId }, pathname: '/place/[placeId]' });
  }, []);

  function openSearch() {
    if (offline) return;
    if (!isSignedIn) { setGate('search'); return; }
    setSelectedId(null);
    setSearching(true);
    sheetRef.current?.snapToIndex(FULL);
  }

  function closeSearch(snapBack: boolean) {
    Keyboard.dismiss();
    setSearching(false);
    setQuery('');
    if (snapBack) sheetRef.current?.snapToIndex(HALF);
  }

  function rememberQuery() {
    const q = query.trim();
    if (!q) return;
    setRecent(previous => [q, ...previous.filter(item => item.toLowerCase() !== q.toLowerCase())].slice(0, MAX_RECENT));
  }

  function handleSheetAnimate(_from: number, toIndex: number, _fromPosition: number, toPosition: number) {
    if (toIndex >= 0 && toIndex < FULL) setMapBottom(Math.max(0, Math.round(height - toPosition)));
  }

  function handleSheetChange(index: number) {
    setSheetIndex(index);
    if (index < FULL && searching) closeSearch(false);
  }

  async function handleLocate() {
    const result = await locate();
    if (!result) return;
    if (!result.ok) { setToast(t(result.reason === 'denied' ? 'home.map.locationDenied' : 'home.map.locationFailed')); return; }
    mapRef.current?.animateToRegion(framedRegion(result.point, 0.02, aspect), reduced ? 0 : 600);
  }

  // Floating map controls ride just above the sheet's top edge.
  const floatStyle = useAnimatedStyle(() => ({ transform: [{ translateY: sheetTop.value }] }));
  const showFloating = !searching && sheetIndex < FULL;
  const credit = selectedPlace?.thumbnail?.attribution_text;
  const initial = profile.name.trim()[0]?.toUpperCase();

  return (
    <View style={styles.screen}>
      <StatusBar style="dark" />

      <HomeMap
        accessibilityLabel={t('home.map.label', { city: cityName ?? '' })}
        bottomPadding={mapBottom}
        initialRegion={initialRegion}
        mapRef={mapRef}
        onSelect={setSelectedId}
        places={markers}
        selectedId={selectedId}
        showsUserLocation={granted}
      />

      <LinearGradient
        colors={['rgba(251,247,240,0.96)', 'rgba(251,247,240,0.7)', 'rgba(251,247,240,0)']}
        pointerEvents="none"
        style={[styles.scrim, { height: insets.top + 200 }]}
      />

      <View pointerEvents="box-none" style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <View pointerEvents="box-none" style={styles.topRow}>
          <Wordmark width={128} />
          <Pressable accessibilityLabel={t('home.profile')} accessibilityRole="button" onPress={() => router.push('/profile')} style={styles.avatar}>
            {initial ? <Text style={styles.avatarText}>{initial}</Text> : <AccountIcon name="person" />}
          </Pressable>
        </View>
        <CityButton cityName={cityName} onPress={() => setCitySheetOpen(true)} />
        <SearchPill cityName={cityName ?? ''} disabled={offline} onPress={openSearch} onVoice={openSearch} />
        {offline ? (
          <View style={styles.offlineHint}>
            <Icon color={colors.ink} name="info" size={16} />
            <Text style={styles.offlineText}>{t('home.search.offlineHint')}</Text>
          </View>
        ) : null}
      </View>

      {showFloating ? (
        <Animated.View pointerEvents="box-none" style={[styles.floating, floatStyle]}>
          <View pointerEvents="box-none" style={styles.floatingInner}>
            {selectedPlace ? <PlacePreviewCard onOpen={openPlace} place={selectedPlace} /> : null}
            <View pointerEvents="box-none" style={styles.controls}>
              {credit ? <View style={styles.credit}>
                <Text numberOfLines={1} style={styles.creditText}>{t('home.map.photoCredit', { credit })}</Text>
              </View> : <View style={styles.creditSpacer} />}
              <CircleButton accessibilityLabel={t('home.map.gps')} icon="navigation" onPress={handleLocate} size={48} />
            </View>
          </View>
        </Animated.View>
      ) : null}

      <BottomSheet
        animatedPosition={sheetTop}
        animateOnMount={!reduced}
        backgroundStyle={styles.sheetBackground}
        bottomInset={0}
        enableDynamicSizing={false}
        handleIndicatorStyle={styles.handle}
        index={HALF}
        keyboardBehavior="extend"
        keyboardBlurBehavior="restore"
        onAnimate={handleSheetAnimate}
        onChange={handleSheetChange}
        overrideReduceMotion={reduced ? ReduceMotion.Always : ReduceMotion.System}
        ref={sheetRef}
        snapPoints={SNAP_POINTS}
        style={styles.sheet}
      >
        <BottomSheetScrollView
          contentContainerStyle={{ paddingBottom: tabBarHeight + spacing.xl }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          stickyHeaderIndices={searching ? [0] : undefined}
        >
          {searching && city ? [
            <View key="header" style={styles.gutter}>
              <SearchHeader
                cityName={cityName ?? ''}
                offline={offline}
                onCancel={() => closeSearch(true)}
                onChangeQuery={setQuery}
                onSubmit={rememberQuery}
                query={query}
              />
            </View>,
            <View key="body" style={styles.gutter}>
              <SearchBody
                city={city}
                offline={offline}
                onChangeCity={() => setCitySheetOpen(true)}
                onOpenPlace={place => { rememberQuery(); openPlace(place.id); }}
                onPickRecent={setQuery}
                query={query}
                recent={recent}
              />
            </View>,
          ] : (
            <HomeSheetContent categoryFilter={categoryFilter} onCategoryChange={setCategoryFilter} onOpenPlace={openPlace} />
          )}
        </BottomSheetScrollView>
      </BottomSheet>

      {toast ? (
        <View accessibilityLiveRegion="polite" pointerEvents="none" style={[styles.toast, elevation.md, { top: insets.top + 8 }]}>
          <Text style={styles.toastText}>{toast}</Text>
        </View>
      ) : null}

      <CitySheet onClose={() => setCitySheetOpen(false)} visible={citySheetOpen} />
      <SignInGate feature={gate} onClose={() => setGate(null)} />
    </View>
  );
}

const styles = StyleSheet.create({
  avatar: {
    alignItems: 'center',
    backgroundColor: colors.sun,
    borderColor: colors.white,
    borderRadius: 26,
    borderWidth: 2,
    height: 52,
    justifyContent: 'center',
    overflow: 'hidden',
    width: 52,
  },
  avatarText: { color: colors.ink, fontFamily: fonts.bold, fontSize: 20 },
  controls: { alignItems: 'flex-end', flexDirection: 'row', gap: 12, justifyContent: 'space-between' },
  credit: {
    backgroundColor: 'rgba(255,255,255,0.88)',
    borderRadius: 8,
    flexShrink: 1,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  creditSpacer: { flex: 1 },
  creditText: { color: colors.ink, fontFamily: fonts.medium, fontSize: 11, lineHeight: 15 },
  floating: { height: 0, left: 0, position: 'absolute', right: 0, top: 0 },
  floatingInner: { bottom: 12, gap: 12, left: GUTTER, position: 'absolute', right: GUTTER - 4 },
  gutter: { backgroundColor: colors.canvas, paddingHorizontal: GUTTER },
  handle: { backgroundColor: '#C9C9C9', height: 4, width: 68 },
  header: { gap: 10, left: 0, paddingHorizontal: GUTTER - 4, position: 'absolute', right: 0, top: 0 },
  offlineHint: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255,255,255,0.94)',
    borderRadius: 14,
    flexDirection: 'row',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  offlineText: { color: colors.ink, flexShrink: 1, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18 },
  scrim: { left: 0, position: 'absolute', right: 0, top: 0 },
  screen: { backgroundColor: colors.canvas, flex: 1 },
  sheet: {
    shadowColor: colors.ink,
    shadowOffset: { height: -4, width: 0 },
    shadowOpacity: 0.08,
    shadowRadius: 14,
  },
  sheetBackground: { backgroundColor: colors.canvas, borderTopLeftRadius: radii.sheet, borderTopRightRadius: radii.sheet },
  toast: {
    alignSelf: 'center',
    backgroundColor: colors.deepOcean,
    borderRadius: 16,
    left: GUTTER,
    paddingHorizontal: 16,
    paddingVertical: 12,
    position: 'absolute',
    right: GUTTER,
  },
  toastText: { color: colors.white, fontFamily: fonts.regular, fontSize: 15, lineHeight: 22, textAlign: 'center' },
  topRow: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', paddingLeft: 4 },
});

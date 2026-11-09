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
import { CircleButton, Icon, Toast } from '../../components/ui';
import { useAccount } from '../../features/account/AccountContext';
import { AccountIcon } from '../../features/account/AccountUI';
import { SignInGate, type GateFeature } from '../../features/auth/SignInGate';
import { CityButton } from '../../features/home/city/CityButton';
import { CitySheet } from '../../features/home/city/CitySheet';
import { useSelectedCity } from '../../features/home/cityStore';
import { useTabBarHeight } from '../../features/home/components/HomeTabBar';
import { HomeMap } from '../../features/home/map/HomeMap';
import { PlacePreviewCard } from '../../features/home/map/PlacePreviewCard';
import { DA_NANG_TRAVEL_BBOX, cityCenter, cityRegion, framedRegion } from '../../features/home/map/region';
import { useLocateMe } from '../../features/home/map/useLocateMe';
import { SearchBody, SearchHeader } from '../../features/home/search/SearchPanel';
import { SearchPill } from '../../features/home/search/SearchPill';
import { HomeSheetContent } from '../../features/home/sections/HomeSheetContent';
import { useIsOffline } from '../../features/home/useNetwork';
import { usePlaceList } from '../../features/home/usePlaces';
import { useReducedMotion } from '../../hooks/useReducedMotion';
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
/** Markers drawn on the Home map: the places nearest the city centre (clustered when they overlap). */
const MAX_MARKERS = 30;
/** Radius of the unfiltered marker set around the city centre, in degrees (~8 km). */
const CORE_RADIUS_DEG = 0.072;
const MAX_RECENT = 5;
const GUTTER = 20;
const elevationFloating = elevation.floating;

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
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [citySheetOpen, setCitySheetOpen] = useState(false);
  const [gate, setGate] = useState<GateFeature | null>(null);
  const [searching, setSearching] = useState(false);
  const [query, setQuery] = useState('');
  /** Recent queries for this session only: memory, never stored or logged. */
  const [recent, setRecent] = useState<string[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const { granted, locate } = useLocateMe();

  // Markers: published places of the selected city, or of the selected category (API-010, filtered on the server).
  // The shared list is keyed by city, category and UI language, so names follow a language switch.
  const { result: markerLoad, retry: retryMarkers } = usePlaceList(city?.id, { categoryCode: categoryFilter, enabled: !offline });
  useEffect(() => { setSelectedId(null); }, [city?.id, categoryFilter]);

  const markers = useMemo(() => {
    if (markerLoad.state !== 'ready' || !city) return [] as Place[];
    // The places nearest the city centre, so the camera frames the dense core instead of far-flung outliers.
    const centre = cityCenter(city.code);
    const distance = (place: Place) => (place.location.latitude - centre.latitude) ** 2 + (place.location.longitude - centre.longitude) ** 2;
    const nearest = [...markerLoad.items].sort((a, b) => distance(a) - distance(b)).slice(0, MAX_MARKERS);
    // Unfiltered: keep the city core (within ~8 km) so the camera does not zoom out to far-flung places such as
    // Mỹ Sơn; a category shows all its places (they are what the user asked for).
    if (categoryFilter) return nearest;
    const core = nearest.filter(place => distance(place) <= CORE_RADIUS_DEG ** 2);
    return core.length >= 6 ? core : nearest;
  }, [categoryFilter, city, markerLoad]);
  const selectedPlace = markers.find(place => place.id === selectedId) ?? null;

  // Fit the camera to the markers actually drawn whenever that set changes (city, category, first load).
  const markerKey = markers.map(place => place.id).join(',');
  useEffect(() => {
    if (!city || !mapReady || markerLoad.state !== 'ready') return;
    const inBounds = markers
      .map(place => place.location)
      .filter(
        p =>
          p.latitude >= DA_NANG_TRAVEL_BBOX.minLat &&
          p.latitude <= DA_NANG_TRAVEL_BBOX.maxLat &&
          p.longitude >= DA_NANG_TRAVEL_BBOX.minLng &&
          p.longitude <= DA_NANG_TRAVEL_BBOX.maxLng,
      );
    const points = inBounds.length > 0 ? inBounds : markers.map(place => place.location);
    if (points.length > 1) {
      mapRef.current?.fitToCoordinates(points, {
        animated: !reduced,
        // Added to mapPadding (which already clears the sheet): keep markers below the floating header.
        edgePadding: { bottom: 24, left: 40, right: 40, top: insets.top + 170 },
      });
    } else {
      const target = points[0];
      mapRef.current?.animateToRegion(target ? framedRegion(target, 0.02, aspect) : cityRegion(city.code, [], aspect), reduced ? 0 : 600);
    }
    // Runs when the drawn set changes, not on resize or motion-setting changes.
  }, [markerKey, markerLoad.state, mapReady]);

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
  const markersFailed = !offline && markerLoad.state === 'error';
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
        onMapReady={() => setMapReady(true)}
        onSelect={setSelectedId}
        places={markers}
        selectedId={selectedId}
        showsUserLocation={granted}
      />

      <LinearGradient
        colors={['rgba(255,255,255,0.96)', 'rgba(255,255,255,0.7)', 'rgba(255,255,255,0)']}
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
        {markersFailed ? (
          <Pressable
            accessibilityHint={t('home.map.retryHint')}
            accessibilityRole="button"
            onPress={retryMarkers}
            style={({ pressed }) => [styles.retryChip, pressed && styles.pressed]}
          >
            <Icon color={colors.danger} name="warning" size={16} />
            <Text style={styles.retryText}>{t('home.map.loadError')}</Text>
            <Text style={styles.retryLink}>{t('home.map.retry')}</Text>
          </Pressable>
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
        android_keyboardInputMode="adjustResize"
        animateOnMount={!reduced}
        backgroundStyle={styles.sheetBackground}
        bottomInset={0}
        enableDynamicSizing={false}
        // While the search field is open the sheet stays at full height: dragging scrolls results and dismisses the
        // keyboard instead of pulling the sheet (and the layout) down. Cancel closes search.
        enableContentPanningGesture={!searching}
        enableHandlePanningGesture={!searching}
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
          bounces={!searching}
          keyboardDismissMode="on-drag"
          keyboardShouldPersistTaps="handled"
          overScrollMode="never"
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

      {toast ? <Toast style={[styles.toast, { top: insets.top + 8 }]} text={toast} tone="info" /> : null}

      <CitySheet onClose={() => setCitySheetOpen(false)} visible={citySheetOpen} />
      <SignInGate feature={gate} onClose={() => setGate(null)} />
    </View>
  );
}

const styles = StyleSheet.create({
  avatar: {
    alignItems: 'center',
    backgroundColor: colors.primary,
    borderColor: colors.white,
    borderRadius: 26,
    borderWidth: 2,
    height: 52,
    justifyContent: 'center',
    overflow: 'hidden',
    width: 52,
  },
  avatarText: { color: colors.white, fontFamily: fonts.bold, fontSize: 20 },
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
  handle: { backgroundColor: colors.hairline, height: 5, width: 44 },
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
  pressed: { opacity: 0.8 },
  retryChip: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: colors.white,
    borderRadius: radii.pill,
    flexDirection: 'row',
    gap: 6,
    minHeight: 40,
    paddingHorizontal: 14,
    ...elevationFloating,
  },
  retryLink: { color: colors.primary, fontFamily: fonts.semibold, fontSize: 14, lineHeight: 19 },
  retryText: { color: colors.ink, fontFamily: fonts.medium, fontSize: 14, lineHeight: 19 },
  scrim: { left: 0, position: 'absolute', right: 0, top: 0 },
  screen: { backgroundColor: colors.canvas, flex: 1 },
  sheet: {
    shadowColor: colors.ink,
    shadowOffset: { height: -4, width: 0 },
    shadowOpacity: 0.08,
    shadowRadius: 14,
  },
  sheetBackground: { backgroundColor: colors.canvas, borderTopLeftRadius: radii.sheet, borderTopRightRadius: radii.sheet },
  toast: { alignSelf: 'center', left: GUTTER, position: 'absolute', right: GUTTER },
  topRow: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', paddingLeft: 4 },
});

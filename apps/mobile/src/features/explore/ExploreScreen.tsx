import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { RefreshControl, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { SectionHeader } from '../../components/ui';
import type { Place } from '../../lib/api/types';
import { colors } from '../../theme/colors';
import { spacing } from '../../theme/spacing';
import { fonts } from '../../theme/typography';
import { useAccount } from '../account/AccountContext';
import { SignInGate } from '../auth/SignInGate';
import { CitySheet } from '../home/city/CitySheet';
import { useSelectedCity } from '../home/cityStore';
import { useTabBarClearance } from '../home/components/HomeTabBar';
import { ErrorBanner, NoticeBanner } from '../home/sections/SheetBanners';
import { useIsOffline } from '../home/useNetwork';
import { EmptyState } from './components/EmptyState';
import { CategoryRow, ExploreSearchBar, ExploreTitle, type ResultView } from './components/ExploreHeader';
import {
  FEATURED_WIDTH,
  FeaturedCard,
  FeaturedSkeleton,
  GridSkeleton,
  ListSkeleton,
  PlaceGridCard,
  PlaceListRow,
} from './components/PlaceCards';
import { useExploreData } from './useExploreData';

const GUTTER = 20;
const GRID_GAP = spacing.sm;
const MAX_FEATURED = 6;
const MAX_CONTENT = 720;

/**
 * SCR-021 Explore tab: city pill, search (signed-in; guests get SCR-040), category chips, grid/list results, and
 * "Featured" + "All places" when there is no query. Guests may browse and open place cards like on Home.
 */
export function ExploreScreen() {
  const { t, i18n } = useTranslation();
  const insets = useSafeAreaInsets();
  const clearance = useTabBarClearance();
  const { width: windowWidth } = useWindowDimensions();
  const offline = useIsOffline();
  const { isSignedIn } = useAccount();
  const { city, loading: cityLoading, error: cityError, reload: reloadCities } = useSelectedCity();

  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<string | null>(null);
  const [view, setView] = useState<ResultView>('grid');
  const [cityOpen, setCityOpen] = useState(false);
  const [gateOpen, setGateOpen] = useState(false);

  const vi = i18n.resolvedLanguage === 'vi';
  const cityName = city ? (vi ? city.name_vi : city.name_en) : null;
  const q = query.trim();
  const searching = isSignedIn && !offline && q.length > 0;

  const data = useExploreData(city?.id, isSignedIn ? query : '', isSignedIn && !offline);
  const { categories, categoryName, places, placesState, refresh, results, searchState } = data;

  // A signed-out session never keeps a typed query; a new city starts unfiltered.
  useEffect(() => { if (!isSignedIn) setQuery(''); }, [isSignedIn]);
  useEffect(() => { setCategory(null); }, [city?.id]);

  const contentWidth = Math.min(windowWidth, MAX_CONTENT) - GUTTER * 2;
  const cardWidth = Math.floor((contentWidth - GRID_GAP) / 2);

  const openPlace = useCallback((place: Place) => {
    router.push({ params: { placeId: place.id }, pathname: '/place/[placeId]' });
  }, []);

  const onRefresh = useCallback(() => {
    if (cityError && !city) reloadCities();
    refresh();
  }, [city, cityError, refresh, reloadCities]);

  const source = searching ? results : places;
  const shown = useMemo(() => (category ? source.filter(p => p.category_code === category) : source), [category, source]);
  const featured = useMemo(() => places.filter(p => p.thumbnail).slice(0, MAX_FEATURED), [places]);

  function renderPlaces(items: Place[]) {
    if (view === 'list') {
      return (
        <View>
          {items.map(place => (
            <PlaceListRow categoryLabel={categoryName(place.category_code)} key={place.id} onPress={() => openPlace(place)} place={place} />
          ))}
        </View>
      );
    }
    return (
      <View style={styles.grid}>
        {items.map(place => (
          <PlaceGridCard categoryLabel={categoryName(place.category_code)} key={place.id} onPress={() => openPlace(place)} place={place} width={cardWidth} />
        ))}
      </View>
    );
  }

  const skeleton = view === 'grid' ? <GridSkeleton width={cardWidth} /> : <ListSkeleton />;
  const changeCity = { label: t('explore.states.changeCity'), onPress: () => setCityOpen(true) };

  let body: ReactNode;
  if (!city) {
    body = cityError && !cityLoading
      ? <ErrorBanner message={t('explore.states.cityError')} onRetry={reloadCities} retryLabel={t('explore.states.retry')} />
      : <Loading label={t('explore.states.loading')}><FeaturedSkeleton />{skeleton}</Loading>;
  } else if (searching) {
    const name = cityName ?? '';
    if (searchState === 'error') {
      body = <ErrorBanner message={t('explore.states.searchError')} onRetry={data.retrySearch} retryLabel={t('explore.states.retry')} />;
    } else if (searchState !== 'done' && results.length === 0) {
      body = <Loading label={t('explore.results.searching')}><StatusLine text={t('explore.results.searching')} />{skeleton}</Loading>;
    } else if (searchState === 'done' && shown.length === 0) {
      body = (
        <EmptyState
          actions={[{ label: t('explore.states.clearSearch'), onPress: () => setQuery('') }, changeCity]}
          body={t('explore.states.emptyQueryBody')}
          icon="search"
          title={t('explore.states.emptyQueryTitle', { city: name, q })}
        />
      );
    } else {
      body = (
        <>
          <StatusLine text={searchState === 'loading' ? t('explore.results.searching') : t('explore.results.count', { city: name, count: shown.length })} />
          {renderPlaces(shown)}
        </>
      );
    }
  } else if (placesState === 'loading' && places.length === 0) {
    body = <Loading label={t('explore.states.loading')}>{category ? null : <FeaturedSkeleton />}{skeleton}</Loading>;
  } else if (placesState === 'error' && places.length === 0) {
    body = offline
      ? <NoticeBanner icon="info" message={t('explore.states.offlineEmpty')} />
      : <ErrorBanner message={t('explore.states.error')} onRetry={data.retryPlaces} retryLabel={t('explore.states.retry')} />;
  } else if (places.length === 0) {
    body = (
      <EmptyState
        actions={[changeCity]}
        body={t('explore.states.comingBody', { city: cityName })}
        icon="map-pin"
        title={t('explore.states.comingTitle', { city: cityName })}
      />
    );
  } else if (category) {
    const label = categoryName(category);
    body = shown.length === 0 ? (
      <EmptyState
        actions={[{ label: t('explore.states.showAll'), onPress: () => setCategory(null) }]}
        body={t('explore.states.emptyCategoryBody')}
        icon="search"
        title={t('explore.states.emptyCategoryTitle', { category: label.toLocaleLowerCase(), city: cityName })}
      />
    ) : (
      <>
        <SectionHeader subtitle={t('explore.all.count', { count: shown.length })} title={label} />
        {renderPlaces(shown)}
      </>
    );
  } else {
    body = (
      <>
        {featured.length > 0 ? (
          <View style={styles.featuredBlock}>
            <SectionHeader subtitle={t('explore.featured.subtitle')} title={t('explore.featured.title', { city: cityName })} />
            <ScrollView
              contentContainerStyle={[styles.carousel, { paddingHorizontal: GUTTER }]}
              decelerationRate="fast"
              horizontal
              showsHorizontalScrollIndicator={false}
              snapToAlignment="start"
              snapToInterval={FEATURED_WIDTH + spacing.md}
              style={styles.bleed}
            >
              {featured.map(place => (
                <FeaturedCard categoryLabel={categoryName(place.category_code)} key={place.id} onPress={() => openPlace(place)} place={place} />
              ))}
            </ScrollView>
          </View>
        ) : null}
        <SectionHeader subtitle={t('explore.all.count', { count: places.length })} title={t('explore.all.title')} />
        {renderPlaces(places)}
      </>
    );
  }

  return (
    <View style={[styles.screen, { paddingTop: insets.top }]}>
      <StatusBar style="dark" />
      <ScrollView
        contentContainerStyle={[styles.content, { paddingBottom: clearance + spacing.lg }]}
        keyboardDismissMode="on-drag"
        keyboardShouldPersistTaps="handled"
        refreshControl={
          <RefreshControl colors={[colors.audioTeal]} onRefresh={onRefresh} refreshing={data.refreshing} tintColor={colors.audioTeal} />
        }
        stickyHeaderIndices={[1]}
      >
        <View style={[styles.inner, styles.head]}>
          <ExploreTitle cityName={cityName} onPickCity={() => setCityOpen(true)} />
        </View>

        <View style={styles.sticky}>
          <View style={styles.inner}>
            <ExploreSearchBar
              cityName={cityName ?? ''}
              guest={!isSignedIn}
              offline={offline}
              onChange={setQuery}
              onChangeView={setView}
              onGuestPress={() => setGateOpen(true)}
              value={query}
              view={view}
            />
          </View>
          <View style={styles.chipsWrap}>
            <CategoryRow categories={categories} gutter={GUTTER} onChange={setCategory} value={category} />
          </View>
        </View>

        <View style={[styles.inner, styles.body]}>
          {offline ? <NoticeBanner icon="info" message={t('explore.states.offline')} /> : null}
          {body}
        </View>
      </ScrollView>

      <CitySheet onClose={() => setCityOpen(false)} visible={cityOpen} />
      <SignInGate feature={gateOpen ? 'search' : null} onClose={() => setGateOpen(false)} />
    </View>
  );
}

function StatusLine({ text }: { text: string }) {
  return <Text accessibilityLiveRegion="polite" accessibilityRole="text" style={styles.status}>{text}</Text>;
}

function Loading({ label, children }: { label: string; children: ReactNode }) {
  return <View accessibilityLabel={label} accessibilityRole="progressbar" style={styles.loading}>{children}</View>;
}

const styles = StyleSheet.create({
  bleed: { marginHorizontal: -GUTTER },
  body: { gap: spacing.md, paddingTop: spacing.md },
  carousel: { gap: spacing.md, paddingBottom: spacing.xs },
  chipsWrap: { alignSelf: 'center', maxWidth: MAX_CONTENT, paddingTop: spacing.sm, width: '100%' },
  content: { flexGrow: 1 },
  featuredBlock: { marginBottom: spacing.xs },
  grid: { columnGap: GRID_GAP, flexDirection: 'row', flexWrap: 'wrap', rowGap: GRID_GAP },
  head: { paddingBottom: spacing.md, paddingTop: spacing.xs },
  inner: { alignSelf: 'center', maxWidth: MAX_CONTENT, paddingHorizontal: GUTTER, width: '100%' },
  loading: { gap: spacing.lg },
  screen: { backgroundColor: colors.canvas, flex: 1 },
  status: { color: colors.textMuted, fontFamily: fonts.regular, fontSize: 14, lineHeight: 20 },
  sticky: {
    backgroundColor: colors.white,
    borderBottomColor: colors.hairline,
    borderBottomWidth: StyleSheet.hairlineWidth,
    paddingBottom: spacing.sm,
    paddingTop: spacing.xs,
  },
});

import { router, useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import { listCategories, listTrips, loadErrorKind, type LoadErrorKind } from '../../../lib/api/source';
import type { Category, Trip } from '../../../lib/api/types';
import { spacing } from '../../../theme/spacing';
import { useAccount } from '../../account/AccountContext';
import { SignInGate, type GateFeature } from '../../auth/SignInGate';
import { isTripToday } from '../../trips/tripDates';
import { useSelectedCity } from '../cityStore';
import { useIsOffline } from '../useNetwork';
import { usePlaceList, usePopulatedCategories } from '../usePlaces';
import { CategoryChips } from './CategoryChips';
import { ExplorePlaces } from './ExplorePlaces';
import { Greeting } from './Greeting';
import { PlanBanner } from './PlanBanner';
import { HomePlaceRails } from './PlaceRail';
import { SavedTrips, SavedTripsGuest, type TripsLoad } from './SavedTrips';
import { ErrorBanner, NoticeBanner } from './SheetBanners';
import { TodayCard } from './TodayCard';
import { cityLabel } from './homeSheetUtils';

/** Horizontal page gutter; horizontal rows scroll edge to edge and pad their content by this much. */
const GUTTER = spacing.lg;

export type HomeSheetContentProps = {
  /** Selected category code, or null for "Tất cả". Owned by `home.tsx` so the map markers share it. */
  categoryFilter: string | null;
  onCategoryChange: (code: string | null) => void;
  onOpenPlace: (placeId: string) => void;
};

/**
 * SCR-008 Home bottom-sheet content (plain View; `home.tsx` wraps it in the sheet's scroll view): offline banner,
 * greeting, Plan banner, Today card, category chips, the Hội An and Food & drink rails, saved trips and "Khám phá {city}".
 */
export function HomeSheetContent({ categoryFilter, onCategoryChange, onOpenPlace }: HomeSheetContentProps): React.JSX.Element {
  const { t, i18n } = useTranslation();
  const isVi = i18n.resolvedLanguage === 'vi';
  const { city, cities, error: cityError, loading: cityLoading, reload: reloadCities } = useSelectedCity();
  const offline = useIsOffline();
  const { isLoaded, isSignedIn, profile } = useAccount();
  const [gate, setGate] = useState<GateFeature | null>(null);
  const cityName = cityLabel(city, isVi);

  // Saved trips (signed-in only). Refreshed quietly when Home regains focus (e.g. after Save on SCR-029).
  const [trips, setTrips] = useState<Trip[]>([]);
  const [tripsState, setTripsState] = useState<TripsLoad>('loading');
  const [tripsError, setTripsError] = useState<LoadErrorKind | null>(null);
  const tripsLoaded = useRef(false);
  const loadTrips = useCallback(async (silent: boolean) => {
    if (!silent) setTripsState('loading');
    try {
      const items = await listTrips();
      setTrips(items.filter(trip => trip.status === 'SAVED').sort((a, b) => b.updated_at.localeCompare(a.updated_at)));
      setTripsState('ready');
      tripsLoaded.current = true;
    } catch (error) {
      // A silent refresh keeps what is shown; otherwise show the error banner (S-1).
      if (!silent || !tripsLoaded.current) { setTripsError(loadErrorKind(error)); setTripsState('error'); }
    }
  }, []);
  useFocusEffect(useCallback(() => {
    if (!isSignedIn) return;
    void loadTrips(tripsLoaded.current);
  }, [isSignedIn, loadTrips]));
  useEffect(() => {
    if (isSignedIn) return;
    tripsLoaded.current = false;
    setTrips([]);
    setTripsState('loading');
  }, [isSignedIn]);

  // Categories (once per connection change); only those with published places are offered (data-driven).
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoriesFailed, setCategoriesFailed] = useState(false);
  useEffect(() => {
    let active = true;
    setCategoriesFailed(false);
    listCategories()
      .then(list => { if (active) setCategories(list); })
      .catch(() => { if (active) setCategoriesFailed(true); });
    return () => { active = false; };
  }, [offline]);
  const cityId = city?.id ?? null;
  const populated = usePopulatedCategories(cityId, categories);

  // Published places of the selected city, or of the selected category (server-side filter, all pages). The list is
  // keyed by city, category and UI language, so names follow a language switch.
  const { result: placesLoad, retry: retryPlaces } = usePlaceList(cityId, { categoryCode: categoryFilter, enabled: !offline });

  const todayTrip = isSignedIn && tripsState === 'ready' ? trips.find(trip => isTripToday(trip)) ?? null : null;
  const todayCity = todayTrip ? cities.find(item => item.id === todayTrip.city_id) ?? null : null;

  const startPlan = () => {
    if (offline) return;
    if (!isSignedIn) { setGate('plan'); return; }
    router.push('/plan/new');
  };

  return (
    <View style={styles.root}>
      {offline ? <View style={styles.inset}><NoticeBanner icon="warning" message={t('homeSheet.offline')} /></View> : null}

      <View style={styles.inset}>
        <Greeting cityName={cityName} name={isSignedIn ? profile.name : null} />
      </View>

      <View style={styles.inset}>
        <PlanBanner cityCode={city?.code ?? null} cityName={cityName} offline={offline} onStart={startPlan} />
      </View>

      {todayTrip ? (
        <View style={styles.inset}>
          <TodayCard cityCode={todayCity?.code ?? null} onOpenPlace={onOpenPlace} trip={todayTrip} />
        </View>
      ) : null}

      {!offline ? (
        <CategoryChips categories={populated ?? []} gutter={GUTTER} loading={populated === null && !categoriesFailed} onChange={onCategoryChange} selected={categoryFilter} />
      ) : null}

      {!offline && city && categoryFilter !== null ? (
        <ExplorePlaces
          cityName={cityName}
          categories={categories}
          categoryCode={categoryFilter}
          errorKind={placesLoad.state === 'error' ? placesLoad.kind : null}
          filtered
          gutter={GUTTER}
          isVi={isVi}
          onOpenPlace={onOpenPlace}
          onRetry={retryPlaces}
          places={placesLoad.state === 'ready' ? placesLoad.items : []}
          state={placesLoad.state}
        />
      ) : null}

      {!offline && city && categoryFilter === null ? (
        <HomePlaceRails categories={categories} cityCode={city.code} cityId={cityId} gutter={GUTTER} isVi={isVi} onOpenPlace={onOpenPlace} populated={populated} />
      ) : null}

      {isLoaded && !isSignedIn && categoryFilter === null ? (
        <SavedTripsGuest gutter={GUTTER} onSignIn={() => setGate('trips')} />
      ) : isSignedIn && categoryFilter === null ? (
        <SavedTrips cities={cities} errorKind={tripsError} gutter={GUTTER} onRetry={() => void loadTrips(false)} state={tripsState} trips={trips} />
      ) : null}

      {!offline && city && categoryFilter === null ? (
        <ExplorePlaces
          cityName={cityName}
          categories={categories}
          categoryCode={null}
          errorKind={placesLoad.state === 'error' ? placesLoad.kind : null}
          filtered={false}
          gutter={GUTTER}
          isVi={isVi}
          onOpenPlace={onOpenPlace}
          onRetry={retryPlaces}
          places={placesLoad.state === 'ready' ? placesLoad.items : []}
          state={placesLoad.state}
        />
      ) : null}

      {!offline && !city && cityError && !cityLoading ? (
        <View style={styles.inset}>
          <ErrorBanner message={t('homeSheet.explore.cityError')} onRetry={reloadCities} retryLabel={t('homeSheet.explore.retry')} />
        </View>
      ) : null}

      <SignInGate feature={gate} onClose={() => setGate(null)} />
    </View>
  );
}

const styles = StyleSheet.create({
  inset: { paddingHorizontal: GUTTER },
  root: { gap: spacing.xl, paddingBottom: spacing.xl, paddingTop: spacing.xs },
});

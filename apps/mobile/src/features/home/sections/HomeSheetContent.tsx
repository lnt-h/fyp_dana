import { router, useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import { listCategories, listTrips, searchPlaces } from '../../../lib/api/source';
import type { Category, Place, Trip } from '../../../lib/api/types';
import { spacing } from '../../../theme/spacing';
import { useAccount } from '../../account/AccountContext';
import { SignInGate, type GateFeature } from '../../auth/SignInGate';
import { isTripToday } from '../../trips/tripDates';
import { useSelectedCity } from '../cityStore';
import { useIsOffline } from '../useNetwork';
import { CategoryChips } from './CategoryChips';
import { ExplorePlaces, type PlacesLoad } from './ExplorePlaces';
import { Greeting } from './Greeting';
import { PlanBanner } from './PlanBanner';
import { SavedTrips, SavedTripsGuest, type TripsLoad } from './SavedTrips';
import { NoticeBanner } from './SheetBanners';
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
 * greeting, Plan banner, Today card, category chips, saved trips and "Khám phá {city}".
 */
export function HomeSheetContent({ categoryFilter, onCategoryChange, onOpenPlace }: HomeSheetContentProps): React.JSX.Element {
  const { t, i18n } = useTranslation();
  const isVi = i18n.resolvedLanguage === 'vi';
  const { city, cities } = useSelectedCity();
  const offline = useIsOffline();
  const { isLoaded, isSignedIn, profile } = useAccount();
  const [gate, setGate] = useState<GateFeature | null>(null);
  const cityName = cityLabel(city, isVi);

  // Saved trips (signed-in only). Refreshed quietly when Home regains focus (e.g. after Save on SCR-029).
  const [trips, setTrips] = useState<Trip[]>([]);
  const [tripsState, setTripsState] = useState<TripsLoad>('loading');
  const tripsLoaded = useRef(false);
  const loadTrips = useCallback(async (silent: boolean) => {
    if (!silent) setTripsState('loading');
    try {
      const items = await listTrips();
      setTrips(items.filter(trip => trip.status === 'SAVED').sort((a, b) => b.updated_at.localeCompare(a.updated_at)));
      setTripsState('ready');
      tripsLoaded.current = true;
    } catch {
      // A silent refresh keeps what is shown; otherwise show the error banner (S-1).
      if (!silent || !tripsLoaded.current) setTripsState('error');
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

  // Categories (once).
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  useEffect(() => {
    let active = true;
    listCategories()
      .then(list => { if (active) setCategories(list); })
      .catch(() => undefined)
      .finally(() => { if (active) setCategoriesLoading(false); });
    return () => { active = false; };
  }, [offline]);

  // Published places of the selected city; re-fetched when the city changes or the connection returns.
  const [places, setPlaces] = useState<Place[]>([]);
  const [placesState, setPlacesState] = useState<PlacesLoad>('loading');
  const [placesAttempt, setPlacesAttempt] = useState(0);
  const cityId = city?.id ?? null;
  useEffect(() => {
    if (!cityId || offline) return;
    let active = true;
    setPlacesState('loading');
    searchPlaces(cityId)
      .then(items => { if (active) { setPlaces(items); setPlacesState('ready'); } })
      .catch(() => { if (active) setPlacesState('error'); });
    return () => { active = false; };
  }, [cityId, offline, placesAttempt]);

  const visiblePlaces = useMemo(
    () => (categoryFilter ? places.filter(place => place.category_code === categoryFilter) : places),
    [categoryFilter, places],
  );

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
        <CategoryChips categories={categories} gutter={GUTTER} loading={categoriesLoading} onChange={onCategoryChange} selected={categoryFilter} />
      ) : null}

      {isLoaded && !isSignedIn ? (
        <SavedTripsGuest gutter={GUTTER} onSignIn={() => setGate('trips')} />
      ) : isSignedIn ? (
        <SavedTrips cities={cities} gutter={GUTTER} onRetry={() => void loadTrips(false)} state={tripsState} trips={trips} />
      ) : null}

      {!offline && city ? (
        <ExplorePlaces
          cityName={cityName}
          filtered={categoryFilter !== null}
          gutter={GUTTER}
          onOpenPlace={onOpenPlace}
          onRetry={() => setPlacesAttempt(n => n + 1)}
          places={visiblePlaces}
          state={placesState}
        />
      ) : null}

      <SignInGate feature={gate} onClose={() => setGate(null)} />
    </View>
  );
}

const styles = StyleSheet.create({
  inset: { paddingHorizontal: GUTTER },
  root: { gap: spacing.xl, paddingBottom: spacing.xl, paddingTop: spacing.xs },
});

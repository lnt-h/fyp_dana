import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { listCategories, loadErrorKind, searchPlaces, type LoadErrorKind } from '../../lib/api/source';
import type { Category, Place, Uuid } from '../../lib/api/types';

export const SEARCH_DEBOUNCE_MS = 300;
export const MAX_QUERY = 120;
const MAX_RESULTS = 20;

export type LoadState = 'loading' | 'ready' | 'error';
export type SearchState = 'idle' | 'loading' | 'done' | 'error';

/**
 * SCR-021 data: categories (API-009), the city's published places (API-010 without `q`) and debounced search results
 * (API-010 with `q`, accent-insensitive server-side). Category filtering is client-side
 * (the search call can send `category_code`; this screen still filters locally).
 */
export function useExploreData(cityId: Uuid | undefined, query: string, searchEnabled: boolean) {
  const { i18n } = useTranslation();
  const locale = i18n.resolvedLanguage;
  const q = query.trim();

  const [categories, setCategories] = useState<Category[]>([]);
  const [places, setPlaces] = useState<Place[]>([]);
  const [placesState, setPlacesState] = useState<LoadState>('loading');
  const [placesError, setPlacesError] = useState<LoadErrorKind | null>(null);
  const [searchError, setSearchError] = useState<LoadErrorKind | null>(null);
  const [results, setResults] = useState<Place[]>([]);
  const [searchState, setSearchState] = useState<SearchState>('idle');
  const [attempt, setAttempt] = useState(0);
  const [searchAttempt, setSearchAttempt] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    let active = true;
    listCategories()
      .then(list => { if (active) setCategories([...list].sort((a, b) => a.sort_order - b.sort_order)); })
      .catch(() => undefined); // chips hidden; the list still works
    return () => { active = false; };
  }, [attempt]);

  // A new city (or language) never shows the previous city's places.
  useEffect(() => {
    setPlaces([]);
    setResults([]);
    setPlacesState('loading');
  }, [cityId, locale]);

  useEffect(() => {
    if (!cityId) { setRefreshing(false); return; }
    let active = true;
    searchPlaces(cityId)
      .then(found => {
        if (!active) return;
        setPlaces(found);
        setPlacesState('ready');
      })
      .catch((error: unknown) => { if (active) { setPlacesError(loadErrorKind(error)); setPlacesState('error'); } })
      .finally(() => { if (active) setRefreshing(false); });
    return () => { active = false; };
  }, [attempt, cityId, locale]);

  useEffect(() => {
    if (!cityId || !q || !searchEnabled) { setSearchState('idle'); return; }
    let active = true;
    setSearchState('loading'); // previous results stay visible while loading
    const timer = setTimeout(() => {
      searchPlaces(cityId, q)
        .then(found => {
          if (!active) return;
          setResults(found.slice(0, MAX_RESULTS));
          setSearchState('done');
        })
        .catch((error: unknown) => { if (active) { setSearchError(loadErrorKind(error)); setSearchState('error'); } });
    }, SEARCH_DEBOUNCE_MS);
    return () => { active = false; clearTimeout(timer); };
  }, [cityId, locale, q, searchAttempt, searchEnabled]);

  const refresh = useCallback(() => {
    setRefreshing(true);
    setAttempt(n => n + 1);
    setSearchAttempt(n => n + 1);
  }, []);
  const retryPlaces = useCallback(() => {
    setPlacesState('loading');
    setAttempt(n => n + 1);
  }, []);
  const retrySearch = useCallback(() => setSearchAttempt(n => n + 1), []);

  const categoryName = useMemo(() => {
    const names = new Map(categories.map(c => [c.code, locale === 'vi' ? c.name_vi : c.name_en]));
    return (code: string) => names.get(code) ?? '';
  }, [categories, locale]);

  return { categories, categoryName, places, placesError, placesState, refresh, refreshing, results, retryPlaces, retrySearch, searchError, searchState };
}

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { listCategories, loadErrorKind, searchPlaces, type LoadErrorKind } from '../../lib/api/source';
import { usePlaceList, usePopulatedCategories } from '../home/usePlaces';
import type { Category, Place, Uuid } from '../../lib/api/types';

export const SEARCH_DEBOUNCE_MS = 300;
export const MAX_QUERY = 120;
const MAX_RESULTS = 20;

export type LoadState = 'loading' | 'ready' | 'error';
export type SearchState = 'idle' | 'loading' | 'done' | 'error';

/**
 * SCR-021 data: categories (API-009, only those with published places), the city's published places or one
 * category's places (API-010 without `q`, all pages, filtered on the server) and debounced search results (API-010 with
 * `q` and the selected category, accent-insensitive server-side). Everything re-fetches on a language switch.
 */
export function useExploreData(cityId: Uuid | undefined, query: string, searchEnabled: boolean, category: string | null) {
  const { i18n } = useTranslation();
  const locale = i18n.resolvedLanguage;
  const q = query.trim();

  const [allCategories, setCategories] = useState<Category[]>([]);
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
  const categories = usePopulatedCategories(cityId, allCategories) ?? [];

  // All places (Featured + All) and, when a chip is selected, that category's places, both from the server.
  const all = usePlaceList(cityId);
  const filtered = usePlaceList(cityId, { categoryCode: category, enabled: !!category });
  const list = category ? filtered : all;
  const { retry: retryAll } = all;
  const { retry: retryFiltered } = filtered;
  const places = list.result.state === 'ready' ? list.result.items : [];
  const featuredSource = all.result.state === 'ready' ? all.result.items : [];
  const truncated = list.result.state === 'ready' && list.result.truncated;
  const placesState: LoadState = list.result.state;
  const placesError = list.result.state === 'error' ? list.result.kind : null;

  useEffect(() => { if (list.result.state !== 'loading') setRefreshing(false); }, [list.result.state]);

  // A new city (or language) never shows the previous city's results.
  useEffect(() => { setResults([]); }, [cityId, locale]);

  useEffect(() => {
    if (!cityId || !q || !searchEnabled) { setSearchState('idle'); return; }
    let active = true;
    setSearchState('loading'); // previous results stay visible while loading
    const timer = setTimeout(() => {
      searchPlaces(cityId, q, category)
        .then(found => {
          if (!active) return;
          setResults(found.slice(0, MAX_RESULTS));
          setSearchState('done');
        })
        .catch((error: unknown) => { if (active) { setSearchError(loadErrorKind(error)); setSearchState('error'); } });
    }, SEARCH_DEBOUNCE_MS);
    return () => { active = false; clearTimeout(timer); };
  }, [category, cityId, locale, q, searchAttempt, searchEnabled]);

  const retryPlaces = useCallback(() => { retryAll(); retryFiltered(); }, [retryAll, retryFiltered]);
  const refresh = useCallback(() => {
    setRefreshing(true);
    setAttempt(n => n + 1);
    retryPlaces();
    setSearchAttempt(n => n + 1);
  }, [retryPlaces]);
  const retrySearch = useCallback(() => setSearchAttempt(n => n + 1), []);

  const categoryName = useMemo(() => {
    const names = new Map(allCategories.map(c => [c.code, locale === 'vi' ? c.name_vi : c.name_en]));
    return (code: string) => names.get(code) ?? '';
  }, [allCategories, locale]);

  return {
    categories, categoryName, featuredSource, places, placesError, placesState, refresh, refreshing, results, retryPlaces, retrySearch, searchError,
    searchState, truncated,
  };
}

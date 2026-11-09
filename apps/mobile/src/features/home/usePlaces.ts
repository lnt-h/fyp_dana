import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { loadErrorKind, populatedCategoryCodes, searchPlacesList, type LoadErrorKind, type PlaceList } from '../../lib/api/source';
import type { Category, Place, Uuid } from '../../lib/api/types';

/** How long a loaded list is reused across Home, its map and Explore before it is fetched again. */
const LIST_TTL_MS = 2 * 60_000;

const listCache = new Map<string, { at: number; list: Promise<PlaceList> }>();

/**
 * One shared, de-duplicated API-010 list per city + category + area + language (all pages up to the bound). Home's map,
 * its sheet and Explore ask for the same list at the same time; this makes it one request.
 */
function loadList(cityId: Uuid, categoryCode: string | null, areaCode: string | null, locale: string, fresh: boolean): Promise<PlaceList> {
  const key = [cityId, categoryCode ?? '', areaCode ?? '', locale].join('|');
  const hit = listCache.get(key);
  if (!fresh && hit && Date.now() - hit.at < LIST_TTL_MS) return hit.list;
  const list = searchPlacesList(cityId, undefined, categoryCode, areaCode);
  listCache.set(key, { at: Date.now(), list });
  list.catch(() => listCache.delete(key));
  return list;
}

export type PlacesLoadState =
  | { state: 'loading' }
  | { state: 'error'; kind: LoadErrorKind }
  | { state: 'ready'; items: Place[]; truncated: boolean };

/**
 * Published places of a city, optionally one category or area, filtered on the server (API-010). Re-fetched when the
 * city, filter or UI language changes (names come back in the request locale). `retry` bypasses the cache.
 */
export function usePlaceList(cityId: Uuid | null | undefined, options: { categoryCode?: string | null; areaCode?: string | null; enabled?: boolean } = {}) {
  const { i18n } = useTranslation();
  const locale = i18n.resolvedLanguage ?? 'vi';
  const categoryCode = options.categoryCode ?? null;
  const areaCode = options.areaCode ?? null;
  const enabled = options.enabled ?? true;
  const [result, setResult] = useState<PlacesLoadState>({ state: 'loading' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!cityId || !enabled) return;
    let active = true;
    setResult({ state: 'loading' });
    loadList(cityId, categoryCode, areaCode, locale, attempt > 0)
      .then(list => { if (active) setResult({ items: list.items, state: 'ready', truncated: list.truncated }); })
      .catch((error: unknown) => { if (active) setResult({ kind: loadErrorKind(error), state: 'error' }); });
    return () => { active = false; };
  }, [areaCode, attempt, categoryCode, cityId, enabled, locale]);

  const retry = useCallback(() => setAttempt(n => n + 1), []);
  return { result, retry };
}

/**
 * Categories that have at least one published place in the city (data-driven: one `limit=1` probe per category,
 * cached). Null while unknown. Empty categories (no food places yet, say) never show as chips, topics or rails.
 */
export function usePopulatedCategories(cityId: Uuid | null | undefined, categories: Category[]): Category[] | null {
  const [codes, setCodes] = useState<Set<string> | null>(null);
  const all = useMemo(() => categories.map(category => category.code), [categories]);
  const key = all.join(',');
  useEffect(() => {
    if (!cityId || all.length === 0) { setCodes(null); return; }
    let active = true;
    populatedCategoryCodes(cityId, all).then(found => { if (active) setCodes(found); }).catch(() => undefined);
    return () => { active = false; };
    // `key` stands for the list of codes.
  }, [cityId, key]);
  return useMemo(
    () => (codes ? [...categories].filter(category => codes.has(category.code)).sort((a, b) => a.sort_order - b.sort_order) : null),
    [categories, codes],
  );
}

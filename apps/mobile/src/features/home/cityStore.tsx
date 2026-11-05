import * as SecureStore from 'expo-secure-store';
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { listCities } from '../../lib/api/source';
import type { City, CityCode } from '../../lib/api/types';

/** Device-local city choice (SCR-008/SCR-020). Not synced to Preferences yet (OQ-108). */
const STORAGE_KEY = 'home.selectedCity';
const DEFAULT_CITY: CityCode = 'hoi-an';

type SelectedCityState = {
  /** Selected city once the list has loaded; null while loading or if the list failed. */
  city: City | null;
  cities: City[];
  loading: boolean;
  error: boolean;
  setCity: (code: CityCode) => void;
  reload: () => void;
};

const SelectedCityContext = createContext<SelectedCityState | null>(null);

export function SelectedCityProvider({ children }: { children: ReactNode }) {
  const [cities, setCities] = useState<City[]>([]);
  const [code, setCode] = useState<CityCode>(DEFAULT_CITY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    SecureStore.getItemAsync(STORAGE_KEY)
      .then(saved => { if (saved) setCode(saved as CityCode); })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(false);
    listCities()
      .then(list => { if (active) setCities(list); })
      .catch(() => { if (active) setError(true); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [attempt]);

  const setCity = useCallback((next: CityCode) => {
    setCode(next);
    SecureStore.setItemAsync(STORAGE_KEY, next).catch(() => undefined);
  }, []);

  const value = useMemo<SelectedCityState>(() => ({
    city: cities.find(item => item.code === code) ?? cities.find(item => item.code === DEFAULT_CITY) ?? null,
    cities,
    error,
    loading,
    reload: () => setAttempt(n => n + 1),
    setCity,
  }), [cities, code, error, loading, setCity]);

  return <SelectedCityContext.Provider value={value}>{children}</SelectedCityContext.Provider>;
}

export function useSelectedCity() {
  const value = useContext(SelectedCityContext);
  if (!value) throw new Error('SelectedCityProvider is required');
  return value;
}

import { useCallback, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import { listTrips } from '../../lib/api/source';

export type TripStats = { trips: number; cities: number; days: number };
type State = { status: 'idle' | 'loading' | 'error' } | { status: 'ready'; stats: TripStats };

/** Profile stats from saved trips only (DRAFT excluded). Refreshes on focus; skipped for guests. */
export function useTripStats(enabled: boolean): State {
  const [state, setState] = useState<State>({ status: enabled ? 'loading' : 'idle' });
  useFocusEffect(useCallback(() => {
    if (!enabled) { setState({ status: 'idle' }); return; }
    let active = true;
    setState(previous => previous.status === 'ready' ? previous : { status: 'loading' });
    listTrips()
      .then(trips => {
        if (!active) return;
        const saved = trips.filter(trip => trip.status === 'SAVED');
        setState({ status: 'ready', stats: {
          trips: saved.length,
          cities: new Set(saved.map(trip => trip.city_id)).size,
          days: saved.reduce((sum, trip) => sum + trip.day_count, 0),
        } });
      })
      .catch(() => { if (active) setState({ status: 'error' }); });
    return () => { active = false; };
  }, [enabled]));
  return state;
}

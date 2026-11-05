import * as Location from 'expo-location';
import { useCallback, useRef, useState } from 'react';

import type { GeoPoint } from '../../../lib/api/types';

export type LocateResult = { ok: true; point: GeoPoint } | { ok: false; reason: 'denied' | 'failed' };

/**
 * One-shot device location for the GPS button (SCR-008). Asks for foreground permission only when called (never on
 * mount), reads the position once, and keeps it on the device: the point only recentres the map and is never stored,
 * logged or sent to the API or AI services (BR-046).
 */
export function useLocateMe() {
  const [granted, setGranted] = useState(false);
  const busy = useRef(false);

  const locate = useCallback(async (): Promise<LocateResult | null> => {
    if (busy.current) return null;
    busy.current = true;
    try {
      const permission = await Location.requestForegroundPermissionsAsync();
      if (permission.status !== Location.PermissionStatus.GRANTED) return { ok: false, reason: 'denied' };
      setGranted(true);
      const position = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      return { ok: true, point: { latitude: position.coords.latitude, longitude: position.coords.longitude } };
    } catch {
      return { ok: false, reason: 'failed' };
    } finally {
      busy.current = false;
    }
  }, []);

  return { granted, locate };
}

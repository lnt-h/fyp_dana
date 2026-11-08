import type { Region } from 'react-native-maps';

import type { CityCode, GeoPoint } from '../../../lib/api/types';

/**
 * Fallback map centres (UI constants only, never sent anywhere or used as place data). Used while places load or when
 * a city has no published places yet; otherwise the centre is the mean of the city's place coordinates.
 */
const FALLBACK_CENTERS: Record<CityCode, GeoPoint & { delta: number }> = {
  'da-nang': { delta: 0.12, latitude: 16.0544, longitude: 108.2022 },
};

/** The city's fallback centre (UI constant; Đà Nẵng when the code is unknown). */
export function cityCenter(code: CityCode | undefined): GeoPoint {
  const { latitude, longitude } = FALLBACK_CENTERS[code ?? 'da-nang'] ?? FALLBACK_CENTERS['da-nang'];
  return { latitude, longitude };
}

/**
 * Vertical position (fraction of screen height from the top) where the focus point should appear: midway between the
 * header over the map and the half-open sheet, so markers are not hidden under either.
 */
const FOCUS_FRACTION = 0.3;

/** `aspect` = map width / height. Shifts a centre south so `point` shows at FOCUS_FRACTION instead of the middle of the map. */
export function framedRegion(point: GeoPoint, delta: number, aspect: number): Region {
  return {
    latitude: point.latitude - (0.5 - FOCUS_FRACTION) * delta,
    latitudeDelta: delta,
    longitude: point.longitude,
    longitudeDelta: delta * aspect,
  };
}

/** Region showing all points (mean centre, padded span) or the city fallback when there are none. */
export function cityRegion(code: CityCode | undefined, points: GeoPoint[], aspect: number): Region {
  if (points.length === 0) {
    const fallback = FALLBACK_CENTERS[code ?? 'da-nang'] ?? FALLBACK_CENTERS['da-nang'];
    return framedRegion(fallback, fallback.delta, aspect);
  }
  const mean = {
    latitude: points.reduce((sum, p) => sum + p.latitude, 0) / points.length,
    longitude: points.reduce((sum, p) => sum + p.longitude, 0) / points.length,
  };
  const lats = points.map(p => p.latitude);
  const lngs = points.map(p => p.longitude);
  const span = Math.max(Math.max(...lats) - Math.min(...lats), (Math.max(...lngs) - Math.min(...lngs)) / aspect);
  return framedRegion(mean, Math.max(span * 3, 0.015), aspect);
}

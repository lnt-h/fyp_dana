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

export const DA_NANG_TRAVEL_BBOX = {
  maxDelta: 0.42,
  maxLat: 16.22,
  maxLng: 108.42,
  minLat: 15.82,
  minLng: 107.95,
};

/** Region showing all points (mean centre, padded span) or the city fallback when there are none. */
export function cityRegion(code: CityCode | undefined, points: GeoPoint[], aspect: number): Region {
  const bbox = DA_NANG_TRAVEL_BBOX;
  const inBounds = points.filter(
    p => p.latitude >= bbox.minLat && p.latitude <= bbox.maxLat && p.longitude >= bbox.minLng && p.longitude <= bbox.maxLng
  );
  const targetPoints = inBounds.length > 0 ? inBounds : points;

  if (targetPoints.length === 0) {
    const fallback = FALLBACK_CENTERS[code ?? 'da-nang'] ?? FALLBACK_CENTERS['da-nang'];
    return framedRegion(fallback, fallback.delta, aspect);
  }
  const mean = {
    latitude: targetPoints.reduce((sum, p) => sum + p.latitude, 0) / targetPoints.length,
    longitude: targetPoints.reduce((sum, p) => sum + p.longitude, 0) / targetPoints.length,
  };
  const lats = targetPoints.map(p => p.latitude);
  const lngs = targetPoints.map(p => p.longitude);
  const span = Math.max(Math.max(...lats) - Math.min(...lats), (Math.max(...lngs) - Math.min(...lngs)) / aspect);
  const delta = Math.min(Math.max(span * 1.35, 0.02), bbox.maxDelta);
  return framedRegion(mean, delta, aspect);
}

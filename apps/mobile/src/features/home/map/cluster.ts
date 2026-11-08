import type { Region } from 'react-native-maps';

import type { Place } from '../../../lib/api/types';

/**
 * Grid divisions across the visible region; markers sharing a cell collapse into one cluster. A phone map is about
 * twice as tall as it is wide, so the cells are ~58 pt squares (7 across, 15 down) — just over one 48 pt marker.
 */
const GRID_X = 7;
const GRID_Y = 15;

export type LatLng = { latitude: number; longitude: number };

export type MapItem =
  | { kind: 'place'; place: Place }
  | { kind: 'cluster'; id: string; coordinate: LatLng; members: Place[] };

/**
 * Simple grid clustering for the small (≤ 30) Home marker set. Cells are anchored at 0,0 so they stay
 * stable while panning and only change on zoom. The selected place is never clustered so its card target stays visible.
 */
export function clusterPlaces(places: Place[], region: Region, selectedId: string | null): MapItem[] {
  const cellLat = region.latitudeDelta / GRID_Y;
  const cellLng = region.longitudeDelta / GRID_X;
  if (!(cellLat > 0) || !(cellLng > 0)) return places.map(place => ({ kind: 'place', place }));

  const cells = new Map<string, Place[]>();
  const items: MapItem[] = [];
  for (const place of places) {
    if (place.id === selectedId) {
      items.push({ kind: 'place', place });
      continue;
    }
    const key = `${Math.floor(place.location.latitude / cellLat)}:${Math.floor(place.location.longitude / cellLng)}`;
    const cell = cells.get(key);
    if (cell) cell.push(place);
    else cells.set(key, [place]);
  }

  for (const members of cells.values()) {
    if (members.length === 1) {
      items.push({ kind: 'place', place: members[0] });
      continue;
    }
    const coordinate = {
      latitude: members.reduce((sum, p) => sum + p.location.latitude, 0) / members.length,
      longitude: members.reduce((sum, p) => sum + p.location.longitude, 0) / members.length,
    };
    // Id from sorted member ids keeps the native marker stable across recomputes with the same members.
    const id = members.map(p => p.id).sort().join('|');
    items.push({ kind: 'cluster', id, coordinate, members });
  }
  return items;
}

/** Region that zooms in on a cluster when its members share (almost) one point and cannot be fitted. */
export function zoomInRegion(center: LatLng, region: Region): Region {
  return { ...center, latitudeDelta: region.latitudeDelta / 4, longitudeDelta: region.longitudeDelta / 4 };
}

/** True when members are spread enough for fitToCoordinates to produce a useful zoom. */
export function hasSpread(members: Place[]): boolean {
  const lats = members.map(p => p.location.latitude);
  const lngs = members.map(p => p.location.longitude);
  return Math.max(...lats) - Math.min(...lats) > 1e-4 || Math.max(...lngs) - Math.min(...lngs) > 1e-4;
}

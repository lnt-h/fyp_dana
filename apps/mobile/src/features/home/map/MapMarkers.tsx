import { useCallback, useMemo, useState, type RefObject } from 'react';
import type MapView from 'react-native-maps';
import type { Details, Region } from 'react-native-maps';

import { useReducedMotion } from '../../../hooks/useReducedMotion';
import type { Place } from '../../../lib/api/types';
import { ClusterMarker } from './ClusterMarker';
import { PlaceMarker } from './PlaceMarker';
import { clusterPlaces, hasSpread, zoomInRegion } from './cluster';

const FIT_PADDING = { bottom: 120, left: 80, right: 80, top: 160 };

/** Tracks the settled map region and returns the clustered marker set plus the region handler for MapView. */
export function useMapClusters(mapRef: RefObject<MapView | null>, initialRegion: Region, places: Place[], selectedId: string | null) {
  const reduced = useReducedMotion();
  const [region, setRegion] = useState(initialRegion);
  const items = useMemo(() => clusterPlaces(places, region, selectedId), [places, region, selectedId]);

  const onRegionChangeComplete = useCallback((next: Region, _details?: Details) => setRegion(next), []);

  const zoomToCluster = useCallback((id: string) => {
    const cluster = items.find(item => item.kind === 'cluster' && item.id === id);
    if (!cluster || cluster.kind !== 'cluster') return;
    if (hasSpread(cluster.members)) {
      mapRef.current?.fitToCoordinates(cluster.members.map(p => p.location), { animated: !reduced, edgePadding: FIT_PADDING });
    } else {
      mapRef.current?.animateToRegion(zoomInRegion(cluster.coordinate, region), reduced ? 0 : 500);
    }
  }, [items, mapRef, reduced, region]);

  return { items, onRegionChangeComplete, zoomToCluster };
}

type Props = {
  items: ReturnType<typeof clusterPlaces>;
  selectedId: string | null;
  onSelect: (placeId: string) => void;
  onClusterPress: (id: string) => void;
};

/** Renders single places as photo markers and grouped places as count badges. */
export function MapMarkers({ items, selectedId, onSelect, onClusterPress }: Props) {
  return (
    <>
      {items.map(item => item.kind === 'place'
        ? <PlaceMarker key={item.place.id} onPress={onSelect} place={item.place} selected={item.place.id === selectedId} />
        : <ClusterMarker coordinate={item.coordinate} count={item.members.length} id={item.id} key={`cluster:${item.id}`} onPress={onClusterPress} />)}
    </>
  );
}

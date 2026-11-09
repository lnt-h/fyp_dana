import { memo, type RefObject } from 'react';
import { StyleSheet } from 'react-native';
import MapView, { type MapPressEvent, type Region } from 'react-native-maps';

import type { Place } from '../../../lib/api/types';
import { MapMarkers, useMapClusters } from './MapMarkers';

type Props = {
  mapRef: RefObject<MapView | null>;
  initialRegion: Region;
  places: Place[];
  selectedId: string | null;
  onSelect: (placeId: string | null) => void;
  /** True only after the user granted foreground location from the GPS button. */
  showsUserLocation: boolean;
  accessibilityLabel: string;
  /** Height covered by the bottom sheet and tab bar, so the map's Legal/attribution stays visible (FR-008). */
  bottomPadding: number;
  /** The native map has laid out; camera moves made before this are dropped. */
  onMapReady?: () => void;
};

/** Full-screen map (platform default provider) with up to 30 published-place markers (category-coloured), grid-clustered when they overlap. */
export const HomeMap = memo(function HomeMap({ mapRef, initialRegion, places, selectedId, onSelect, showsUserLocation, accessibilityLabel, bottomPadding, onMapReady }: Props) {
  const clusters = useMapClusters(mapRef, initialRegion, places, selectedId);

  function handleMapPress(event: MapPressEvent) {
    if (event.nativeEvent.action === 'marker-press') return;
    onSelect(null);
  }

  return (
    <MapView
      accessibilityLabel={accessibilityLabel}
      initialRegion={initialRegion}
      mapPadding={{ bottom: bottomPadding, left: 0, right: 0, top: 0 }}
      onMapReady={onMapReady}
      onPress={handleMapPress}
      onRegionChangeComplete={clusters.onRegionChangeComplete}
      pitchEnabled={false}
      ref={mapRef}
      rotateEnabled={false}
      showsCompass={false}
      showsMyLocationButton={false}
      showsPointsOfInterests={false}
      showsUserLocation={showsUserLocation}
      style={StyleSheet.absoluteFill}
      toolbarEnabled={false}
    >
      <MapMarkers items={clusters.items} onClusterPress={clusters.zoomToCluster} onSelect={onSelect} selectedId={selectedId} />
    </MapView>
  );
});

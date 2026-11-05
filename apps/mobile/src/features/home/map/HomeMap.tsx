import { memo, type RefObject } from 'react';
import { StyleSheet } from 'react-native';
import MapView, { type MapPressEvent, type Region } from 'react-native-maps';

import type { Place } from '../../../lib/api/types';
import { PlaceMarker } from './PlaceMarker';

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
};

/** Full-screen map (platform default provider) with up to 20 published-place markers. */
export const HomeMap = memo(function HomeMap({ mapRef, initialRegion, places, selectedId, onSelect, showsUserLocation, accessibilityLabel, bottomPadding }: Props) {
  function handleMapPress(event: MapPressEvent) {
    if (event.nativeEvent.action === 'marker-press') return;
    onSelect(null);
  }

  return (
    <MapView
      accessibilityLabel={accessibilityLabel}
      initialRegion={initialRegion}
      mapPadding={{ bottom: bottomPadding, left: 0, right: 0, top: 0 }}
      onPress={handleMapPress}
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
      {places.map(place => (
        <PlaceMarker key={place.id} onPress={onSelect} place={place} selected={place.id === selectedId} />
      ))}
    </MapView>
  );
});

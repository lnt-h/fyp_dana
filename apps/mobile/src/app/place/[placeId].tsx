import { useLocalSearchParams } from 'expo-router';

import { PlaceScreen } from '../../features/place/PlaceScreen';

/** SCR-033 Place card (`/place/[placeId]`). */
export default function PlaceRoute() {
  const { placeId } = useLocalSearchParams<{ placeId: string }>();
  return <PlaceScreen key={placeId} placeId={placeId} />;
}

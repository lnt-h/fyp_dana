import { useLocalSearchParams } from 'expo-router';

import { TodayScreen } from '../../../features/today/TodayScreen';

/** SCR-032 Today (`/trip/[tripId]/today`). */
export default function TodayRoute() {
  const { tripId } = useLocalSearchParams<{ tripId: string }>();
  return <TodayScreen key={tripId} tripId={tripId} />;
}

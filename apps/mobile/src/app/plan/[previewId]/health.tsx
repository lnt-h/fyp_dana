/** SCR-026 Plan Health detail for one preview (route `/plan/[previewId]/health`). */
import { useLocalSearchParams } from 'expo-router';
import { HealthDetailScreen } from '../../../features/planner/health/HealthDetailScreen';

export default function PlanHealthRoute() {
  const { previewId } = useLocalSearchParams<{ previewId: string }>();
  return <HealthDetailScreen previewId={previewId} />;
}

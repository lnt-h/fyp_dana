import { GenerationProgressScreen } from '../../../features/planner/progress/GenerationProgressScreen';

/** SCR-023 Generation progress (until `preview_ready`, then SCR-024 at `/plan/[previewId]/proposal`). */
export default function PlanProgressRoute() {
  return <GenerationProgressScreen />;
}

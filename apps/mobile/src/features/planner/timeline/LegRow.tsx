import type { Leg } from '../../../lib/api/types';
import { RailLeg } from './TimeRail';

/** Kept for existing call sites: a leg is now drawn on the timeline's left rail (`RailLeg`). */
export function LegRow({ leg }: { leg: Leg }) {
  return <RailLeg leg={leg} />;
}

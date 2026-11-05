/**
 * Groups the server's Plan Health reasons for display. Health itself (`plan_health`) is computed by the server; the
 * client only lists the conflicts it was given (preview `health_reasons`, stop and leg `conflicts`).
 */
import type { Conflict, Uuid } from '../../../lib/api/types';
import type { NumberedDay } from '../timeline/model';

export type HealthIssue = Conflict & {
  key: string;
  dayIndex?: number;
  stopId?: Uuid;
  stopNumber?: number;
  stopName?: string;
  /** Server times of the stop, for the detail line (never computed). */
  arrival?: string | null;
  departure?: string | null;
  placeId?: Uuid;
  /** Leg issues: the stop the leg arrives at (its incoming-leg mode is what SCR-027 edits). */
  toStopId?: Uuid;
  toStopNumber?: number;
  toStopName?: string;
  source: 'stop' | 'leg' | 'preview';
};

export function collectIssues(days: NumberedDay[], healthReasons: Conflict[] = []): HealthIssue[] {
  const issues: HealthIssue[] = [];
  for (const day of days) {
    for (const stop of day.stops) {
      (stop.conflicts ?? []).forEach((conflict, index) => issues.push({
        ...conflict, arrival: stop.planned_arrival, dayIndex: day.day_index, departure: stop.planned_departure, key: `stop-${stop.id}-${index}`,
        placeId: stop.place_id ?? undefined, source: 'stop', stopId: stop.id, stopName: stop.name, stopNumber: stop.number,
      }));
    }
    for (const leg of day.legs) {
      const from = day.stops.find(stop => stop.id === leg.from_stop_id);
      const to = day.stops.find(stop => stop.id === leg.to_stop_id);
      (leg.conflicts ?? []).forEach((conflict, index) => issues.push({
        ...conflict, dayIndex: day.day_index, key: `leg-${leg.from_stop_id}-${leg.to_stop_id}-${index}`, source: 'leg', stopId: from?.id, stopName: from?.name,
        stopNumber: from?.number, toStopId: to?.id, toStopName: to?.name, toStopNumber: to?.number,
      }));
    }
  }
  // Preview-level reasons summarise the same conflicts; keep only those not already listed with stop context.
  healthReasons.forEach((reason, index) => {
    if (!issues.some(issue => issue.type === reason.type && issue.severity === reason.severity)) {
      issues.push({ ...reason, key: `preview-${index}`, source: 'preview' });
    }
  });
  const rank = (issue: HealthIssue) => (issue.severity === 'BLOCKING' ? 0 : 1);
  return issues.sort((a, b) => rank(a) - rank(b) || (a.dayIndex ?? 0) - (b.dayIndex ?? 0) || (a.stopNumber ?? 0) - (b.stopNumber ?? 0));
}

export function countIssues(issues: HealthIssue[]) {
  const blocking = issues.filter(issue => issue.severity === 'BLOCKING').length;
  return { blocking, warnings: issues.length - blocking };
}

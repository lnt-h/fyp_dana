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
  /** Stops named by the conflict's `stop_ids` (e.g. WEB_PLACE_* or calendar rules), resolved from the plan. */
  affectedStops?: { id: Uuid; name: string; number: number; dayIndex: number }[];
  source: 'stop' | 'leg' | 'preview';
};

function affected(days: NumberedDay[], stopIds: Uuid[] | undefined): HealthIssue['affectedStops'] {
  if (!stopIds?.length) return undefined;
  const list = days.flatMap(day => day.stops.filter(stop => stopIds.includes(stop.id)).map(stop => ({ dayIndex: day.day_index, id: stop.id, name: stop.name, number: stop.number })));
  return list.length ? list : undefined;
}

/** INFO conflicts (e.g. `LEG_ESTIMATED`) are notices: never warnings, never counted, never change Plan Health. */
export function isNotice(conflict: Pick<Conflict, 'severity'>): boolean {
  return conflict.severity === 'INFO';
}

/**
 * Disclosures, not plan problems (DEC-023 estimates, DEC-030 unknown hours): never a chip, never counted, never listed
 * as an issue, whatever severity an older server sends. Unknown hours are aggregated into one quiet note instead.
 */
const QUIET_TYPES: ReadonlySet<Conflict['type']> = new Set(['OPENING_HOURS_UNKNOWN', 'LEG_ESTIMATED']);

/** A real problem: WARNING or BLOCKING, and not a disclosure. Only these get stop chips and count in the pill. */
export function isProblem(conflict: Pick<Conflict, 'severity' | 'type'>): boolean {
  return !isNotice(conflict) && !QUIET_TYPES.has(conflict.type);
}

/** Number of stops whose opening hours are not listed (one quiet note on the health detail, never per stop). */
export function unknownHoursStopCount(days: NumberedDay[], healthReasons: Conflict[] = []): number {
  const ids = new Set<Uuid>();
  days.forEach(day => day.stops.forEach(stop => {
    if ((stop.conflicts ?? []).some(conflict => conflict.type === 'OPENING_HOURS_UNKNOWN')) ids.add(stop.id);
  }));
  const planned = new Set(days.flatMap(day => day.stops.map(stop => stop.id)));
  healthReasons.filter(reason => reason.type === 'OPENING_HOURS_UNKNOWN').forEach(reason => (reason.stop_ids ?? []).forEach(id => { if (planned.has(id)) ids.add(id); }));
  return ids.size;
}

/** Real problems (BLOCKING first, then WARNING) with their stop context; notices and disclosures are left out. */
export function collectIssues(days: NumberedDay[], healthReasons: Conflict[] = []): HealthIssue[] {
  const issues: HealthIssue[] = [];
  for (const day of days) {
    for (const stop of day.stops) {
      (stop.conflicts ?? []).forEach((conflict, index) => isProblem(conflict) && issues.push({
        ...conflict, affectedStops: affected(days, conflict.stop_ids?.filter(id => id !== stop.id)), arrival: stop.planned_arrival, dayIndex: day.day_index, departure: stop.planned_departure, key: `stop-${stop.id}-${index}`,
        placeId: stop.place_id ?? undefined, source: 'stop', stopId: stop.id, stopName: stop.name, stopNumber: stop.number,
      }));
    }
    for (const leg of day.legs) {
      const from = day.stops.find(stop => stop.id === leg.from_stop_id);
      const to = day.stops.find(stop => stop.id === leg.to_stop_id);
      (leg.conflicts ?? []).forEach((conflict, index) => isProblem(conflict) && issues.push({
        ...conflict, affectedStops: affected(days, conflict.stop_ids), dayIndex: day.day_index, key: `leg-${leg.from_stop_id}-${leg.to_stop_id}-${index}`, source: 'leg', stopId: from?.id, stopName: from?.name,
        stopNumber: from?.number, toStopId: to?.id, toStopName: to?.name, toStopNumber: to?.number,
      }));
    }
  }
  // Preview-level reasons summarise the same conflicts; keep only those not already listed with stop context. A reason
  // naming one stop (`stop_ids`) gets that stop's context so it can be shown and jumped to.
  healthReasons.forEach((reason, index) => {
    if (!isProblem(reason)) return;
    const sameRule = (issue: HealthIssue) => issue.type === reason.type && issue.severity === reason.severity
      && (issue.rule_id ?? null) === (reason.rule_id ?? null) && (issue.date ?? null) === (reason.date ?? null);
    if (issues.some(sameRule)) return;
    const stops = affected(days, reason.stop_ids);
    const single = stops?.length === 1 ? stops[0] : null;
    issues.push({
      ...reason, affectedStops: single ? undefined : stops, dayIndex: single?.dayIndex, key: `preview-${index}`, source: 'preview',
      stopId: single?.id, stopName: single?.name, stopNumber: single?.number,
    });
  });
  const rank = (issue: HealthIssue) => (issue.severity === 'BLOCKING' ? 0 : 1);
  return issues.sort((a, b) => rank(a) - rank(b) || (a.dayIndex ?? 0) - (b.dayIndex ?? 0) || (a.stopNumber ?? 0) - (b.stopNumber ?? 0));
}

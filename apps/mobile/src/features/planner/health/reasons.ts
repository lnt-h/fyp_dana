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

/** One neutral notice per conflict type, with the days it applies to (an estimated leg repeats on every leg). */
export type HealthNotice = { type: Conflict['type']; message?: string; dayIndexes: number[] };

export function collectNotices(days: NumberedDay[], healthReasons: Conflict[] = []): HealthNotice[] {
  const byType = new Map<Conflict['type'], HealthNotice>();
  const add = (conflict: Conflict, dayIndex?: number) => {
    if (!isNotice(conflict)) return;
    const notice = byType.get(conflict.type) ?? { dayIndexes: [], message: conflict.message, type: conflict.type };
    if (dayIndex != null && !notice.dayIndexes.includes(dayIndex)) notice.dayIndexes.push(dayIndex);
    byType.set(conflict.type, notice);
  };
  for (const day of days) {
    day.stops.forEach(stop => (stop.conflicts ?? []).forEach(conflict => add(conflict, day.day_index)));
    day.legs.forEach(leg => (leg.conflicts ?? []).forEach(conflict => add(conflict, day.day_index)));
  }
  healthReasons.forEach(reason => add(reason));
  return [...byType.values()].map(notice => ({ ...notice, dayIndexes: [...notice.dayIndexes].sort((a, b) => a - b) }));
}

/** BLOCKING and WARNING conflicts with their stop context; INFO notices are left to `collectNotices`. */
export function collectIssues(days: NumberedDay[], healthReasons: Conflict[] = []): HealthIssue[] {
  const issues: HealthIssue[] = [];
  for (const day of days) {
    for (const stop of day.stops) {
      (stop.conflicts ?? []).forEach((conflict, index) => !isNotice(conflict) && issues.push({
        ...conflict, affectedStops: affected(days, conflict.stop_ids?.filter(id => id !== stop.id)), arrival: stop.planned_arrival, dayIndex: day.day_index, departure: stop.planned_departure, key: `stop-${stop.id}-${index}`,
        placeId: stop.place_id ?? undefined, source: 'stop', stopId: stop.id, stopName: stop.name, stopNumber: stop.number,
      }));
    }
    for (const leg of day.legs) {
      const from = day.stops.find(stop => stop.id === leg.from_stop_id);
      const to = day.stops.find(stop => stop.id === leg.to_stop_id);
      (leg.conflicts ?? []).forEach((conflict, index) => !isNotice(conflict) && issues.push({
        ...conflict, affectedStops: affected(days, conflict.stop_ids), dayIndex: day.day_index, key: `leg-${leg.from_stop_id}-${leg.to_stop_id}-${index}`, source: 'leg', stopId: from?.id, stopName: from?.name,
        stopNumber: from?.number, toStopId: to?.id, toStopName: to?.name, toStopNumber: to?.number,
      }));
    }
  }
  // Preview-level reasons summarise the same conflicts; keep only those not already listed with stop context. A reason
  // naming one stop (`stop_ids`) gets that stop's context so it can be shown and jumped to.
  healthReasons.forEach((reason, index) => {
    if (isNotice(reason)) return;
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

export function countIssues(issues: HealthIssue[]) {
  const blocking = issues.filter(issue => issue.severity === 'BLOCKING').length;
  return { blocking, warnings: issues.length - blocking };
}

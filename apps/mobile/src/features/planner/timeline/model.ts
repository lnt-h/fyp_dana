import type { Day, Leg, LegAvailability, Stop, Uuid } from '../../../lib/api/types';

/** A stop with its display number; numbers run on across days (day 2 continues after day 1's last stop). */
export type NumberedStop = Stop & { number: number; dayIndex: number };

export type NumberedDay = Omit<Day, 'stops'> & { stops: NumberedStop[] };

/** Orders days and stops as served and assigns continuous display numbers (shared by the map pins and timeline). */
export function numberDays(days: Day[]): NumberedDay[] {
  let next = 1;
  return [...days]
    .sort((a, b) => a.day_index - b.day_index)
    .map(day => ({
      ...day,
      stops: [...day.stops]
        .sort((a, b) => a.ordinal - b.ordinal)
        .map(stop => ({ ...stop, number: next++, dayIndex: day.day_index })),
    }));
}

/** The leg leaving `stopId`, if the server supplied one. */
export function outgoingLeg(day: NumberedDay, stopId: Uuid): Leg | undefined {
  return day.legs.find(leg => leg.from_stop_id === stopId);
}

/** UNAVAILABLE and EXPIRED legs carry no usable measurement and are never estimated (BRU-006). */
export function isMeasured(availability: LegAvailability): boolean {
  return availability === 'AVAILABLE';
}

/** True when the stop itself carries a BLOCKING conflict from the server. */
export function isStopBlocked(stop: Stop): boolean {
  return (stop.conflicts ?? []).some(conflict => conflict.severity === 'BLOCKING');
}

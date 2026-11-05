import { Linking, Platform } from 'react-native';

import type { Day, Leg, Stop, Trip } from '../../lib/api/types';
import { timeOfDay } from '../home/sections/homeSheetUtils';
import { todayInVietnam, tripEnd, tripStart } from '../trips/tripDates';

/** `today`: the device date (Asia/Ho_Chi_Minh) is inside the trip; otherwise day 1 is shown with a line (FR-055). */
export type DayMode = 'today' | 'before' | 'after';

export function pickDay(trip: Trip, now = Date.now()): { dayIndex: number; mode: DayMode } {
  const today = todayInVietnam(now).getTime();
  if (today < tripStart(trip).getTime()) return { dayIndex: 1, mode: 'before' };
  if (today > tripEnd(trip).getTime()) return { dayIndex: 1, mode: 'after' };
  return { dayIndex: Math.round((today - tripStart(trip).getTime()) / 86_400_000) + 1, mode: 'today' };
}

export type StopStatus = 'done' | 'current' | 'upcoming';

export type TimedStop = {
  stop: Stop;
  arrival: { label: string; minutes: number } | null;
  departure: { label: string; minutes: number } | null;
  status: StopStatus;
};

/**
 * Status from the itinerary's own times compared with the clock (no new times are computed): done once the planned
 * departure has passed, current between arrival and departure. Outside the trip dates everything is upcoming.
 */
export function timeStops(day: Day | undefined, mode: DayMode, nowMinutes: number): TimedStop[] {
  if (!day) return [];
  return [...day.stops].sort((a, b) => a.ordinal - b.ordinal).map(stop => {
    const arrival = timeOfDay(stop.planned_arrival);
    const departure = timeOfDay(stop.planned_departure);
    let status: StopStatus = 'upcoming';
    if (mode === 'today') {
      if (departure && departure.minutes <= nowMinutes) status = 'done';
      else if (arrival && arrival.minutes <= nowMinutes) status = 'current';
    }
    return { arrival, departure, status, stop };
  });
}

/** The stop to feature: the current one, else the next upcoming; null when the day is over or empty. */
export function focusStop(stops: TimedStop[]): TimedStop | null {
  return stops.find(item => item.status === 'current') ?? stops.find(item => item.status === 'upcoming') ?? null;
}

/** Leg that leaves `stop` within the day (legs come from Google Routes only). */
export function legAfter(day: Day | undefined, stop: Stop): Leg | undefined {
  return day?.legs.find(leg => leg.from_stop_id === stop.id);
}

/** Opens the platform maps app at the stop's published coordinates (no device location involved). */
export async function openDirections(stop: Stop): Promise<boolean> {
  const dest = `${stop.location.latitude},${stop.location.longitude}`;
  const google = `https://www.google.com/maps/dir/?api=1&destination=${dest}`;
  const apple = `http://maps.apple.com/?daddr=${dest}`;
  try {
    await Linking.openURL(Platform.OS === 'ios' ? apple : google);
    return true;
  } catch {
    try {
      await Linking.openURL(google);
      return true;
    } catch {
      return false;
    }
  }
}

import { router } from 'expo-router';

import type { City, TripDetail } from '../../../lib/api/types';

/** Minutes since midnight in Asia/Ho_Chi_Minh (UTC+7, no daylight saving). */
export function vietnamMinutesNow(now = Date.now()): number {
  const local = new Date(now + 7 * 3_600_000);
  return local.getUTCHours() * 60 + local.getUTCMinutes();
}

export type DayPart = 'morning' | 'afternoon' | 'evening';

/** Greeting period by the hour in Asia/Ho_Chi_Minh: 04–11 morning, 12–17 afternoon, otherwise evening. */
export function dayPartNow(now = Date.now()): DayPart {
  const hour = Math.floor(vietnamMinutesNow(now) / 60);
  if (hour >= 4 && hour < 12) return 'morning';
  if (hour >= 12 && hour < 18) return 'afternoon';
  return 'evening';
}

/**
 * Wall-clock `HH:MM` of an ISO date-time as authored (the API gives stop times with the city offset, +07:00).
 * Reads the string only; no time arithmetic.
 */
export function timeOfDay(value: string | null | undefined): { label: string; minutes: number } | null {
  const match = value ? /T(\d{2}):(\d{2})/.exec(value) : null;
  if (!match) return null;
  return { label: `${match[1]}:${match[2]}`, minutes: Number(match[1]) * 60 + Number(match[2]) };
}

export function cityLabel(city: City | null | undefined, isVi: boolean): string {
  if (!city) return '';
  return isVi ? city.name_vi : city.name_en;
}

/** Same navigation as SCR-031: a draft resumes its preview; a saved trip opens SCR-024 in read mode. */
export function openTripDetail(detail: TripDetail) {
  const previewId = detail.active_preview_id ?? detail.id;
  router.push({ params: { mode: detail.active_preview_id ? 'draft' : 'saved', previewId, tripId: detail.id }, pathname: '/plan/[previewId]/proposal' });
}

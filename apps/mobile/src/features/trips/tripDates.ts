import type { TFunction } from 'i18next';

import type { IsoDate, Trip } from '../../lib/api/types';

const weekdayKeys = [
  'trips.weekday.sun', 'trips.weekday.mon', 'trips.weekday.tue', 'trips.weekday.wed',
  'trips.weekday.thu', 'trips.weekday.fri', 'trips.weekday.sat',
] as const;
const monthKeys = [
  'trips.month.jan', 'trips.month.feb', 'trips.month.mar', 'trips.month.apr', 'trips.month.may', 'trips.month.jun',
  'trips.month.jul', 'trips.month.aug', 'trips.month.sep', 'trips.month.oct', 'trips.month.nov', 'trips.month.dec',
] as const;

/** Trip dates are calendar dates in the city's zone (Asia/Ho_Chi_Minh); handle them as UTC midnights so no device offset applies. */
function parseDate(value: IsoDate): Date {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

function addDays(date: Date, days: number): Date {
  return new Date(date.getTime() + days * 86_400_000);
}

/** Today in Asia/Ho_Chi_Minh (UTC+7, no daylight saving) as a UTC midnight. */
export function todayInVietnam(now = Date.now()): Date {
  const local = new Date(now + 7 * 3_600_000);
  return new Date(Date.UTC(local.getUTCFullYear(), local.getUTCMonth(), local.getUTCDate()));
}

export function tripStart(trip: Trip): Date {
  return parseDate(trip.start_date);
}

export function tripEnd(trip: Trip): Date {
  return addDays(parseDate(trip.start_date), trip.day_count - 1);
}

/** PAST once the last day (`start_date + day_count − 1`) is before today in Asia/Ho_Chi_Minh (SCR-031). */
export function isPastTrip(trip: Trip, today = todayInVietnam()): boolean {
  return tripEnd(trip).getTime() < today.getTime();
}

/** True when the trip's dates include today (Today chip, SCR-031). */
export function isTripToday(trip: Trip, today = todayInVietnam()): boolean {
  return tripStart(trip).getTime() <= today.getTime() && today.getTime() <= tripEnd(trip).getTime();
}

function formatDay(t: TFunction, date: Date, withYear: boolean): string {
  const d = date.getUTCDate();
  const params = {
    d: String(d),
    dd: String(d).padStart(2, '0'),
    month: t(monthKeys[date.getUTCMonth()]),
    weekday: t(weekdayKeys[date.getUTCDay()]),
    year: String(date.getUTCFullYear()),
  };
  return withYear ? t('trips.date.dayYear', params) : t('trips.date.day', params);
}

/** `T7 16/01 – CN 17/01/2027` (vi) or `Sat 16 Jan – Sun 17 Jan 2027` (en); one-day trips show a single date. */
export function formatTripDates(t: TFunction, trip: Trip): string {
  const start = tripStart(trip);
  const end = tripEnd(trip);
  if (trip.day_count === 1) return formatDay(t, start, true);
  const sameYear = start.getUTCFullYear() === end.getUTCFullYear();
  return t('trips.date.range', { end: formatDay(t, end, true), start: formatDay(t, start, !sameYear) });
}

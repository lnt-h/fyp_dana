import type { IsoDate, LocalTime } from '../../../lib/api/types';

/** Asia/Ho_Chi_Minh is UTC+7 all year (no DST), so wall-clock values are derived arithmetically. */
const VN_OFFSET_MS = 7 * 60 * 60 * 1000;
export const VN_TIME_ZONE = 'Asia/Ho_Chi_Minh';

const pad = (n: number) => String(n).padStart(2, '0');

/** Calendar date in Viet Nam for an instant, as `YYYY-MM-DD`. */
export function vnIsoDate(instant: Date): IsoDate {
  const shifted = new Date(instant.getTime() + VN_OFFSET_MS);
  return `${shifted.getUTCFullYear()}-${pad(shifted.getUTCMonth() + 1)}-${pad(shifted.getUTCDate())}`;
}

/** Wall-clock `HH:MM` (24 h) in Viet Nam for an instant. */
export function vnLocalTime(instant: Date): LocalTime {
  const shifted = new Date(instant.getTime() + VN_OFFSET_MS);
  return `${pad(shifted.getUTCHours())}:${pad(shifted.getUTCMinutes())}`;
}

/** Instant at noon Viet Nam time on `date` (noon keeps the picker away from day edges). */
export function dateFromIso(date: IsoDate): Date {
  const [y, m, d] = date.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d, 12) - VN_OFFSET_MS);
}

/** Instant at `time` Viet Nam time on an arbitrary fixed day (only the wall clock matters). */
export function dateFromLocalTime(time: LocalTime): Date {
  const [h, min] = time.split(':').map(Number);
  return new Date(Date.UTC(2027, 0, 1, h, min) - VN_OFFSET_MS);
}

export const todayVn = (): IsoDate => vnIsoDate(new Date());

/** 0 = Sunday … 6 = Saturday for a calendar date. */
export function weekdayOf(date: IsoDate): number {
  const [y, m, d] = date.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d)).getUTCDay();
}

/** `16/01/2027` (day/month/year, both locales). */
export function dayMonthYear(date: IsoDate): string {
  const [y, m, d] = date.split('-');
  return `${d}/${m}/${y}`;
}

export const minutesOf = (time: LocalTime) => {
  const [h, m] = time.split(':').map(Number);
  return h * 60 + m;
};

/**
 * Display formatting only. Times, distances and durations always come from the preview payload (server, Google
 * Routes); nothing here estimates or derives a planner value.
 */
import type { AppLocale } from '../../../i18n';
import type { IsoDate, IsoDateTime } from '../../../lib/api/types';

/** Asia/Ho_Chi_Minh is UTC+7 with no daylight saving time. */
const VIETNAM_OFFSET_MS = 7 * 60 * 60 * 1000;

const pad = (value: number) => value.toString().padStart(2, '0');

/** `HH:mm`, 24-hour, in Asia/Ho_Chi_Minh; null when the value is missing or unparsable. */
export function formatTime(value?: IsoDateTime | null): string | null {
  if (!value) return null;
  const ms = Date.parse(value);
  if (Number.isNaN(ms)) return null;
  const local = new Date(ms + VIETNAM_OFFSET_MS);
  return `${pad(local.getUTCHours())}:${pad(local.getUTCMinutes())}`;
}

/** Short calendar date for day tabs: `16/01` (vi) or `16 Jan` (en). */
export function formatShortDate(date: IsoDate, locale: AppLocale): string {
  const [year, month, day] = date.split('-').map(Number);
  if (!year || !month || !day) return date;
  if (locale === 'vi') return `${pad(day)}/${pad(month)}`;
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${day} ${months[month - 1] ?? ''}`.trim();
}

/** Calendar date of day `dayIndex` (1-based) of a trip starting on `startDate`. */
export function dayDate(startDate: IsoDate, dayIndex: number): IsoDate {
  const ms = Date.parse(`${startDate}T00:00:00Z`);
  if (Number.isNaN(ms)) return startDate;
  return new Date(ms + (dayIndex - 1) * 86_400_000).toISOString().slice(0, 10);
}

/** `250 m` below one kilometre, otherwise `6,8 km` (vi) / `6.8 km` (en). */
export function formatDistance(meters: number, locale: AppLocale): string {
  if (meters < 1000) return `${Math.round(meters)} m`;
  const km = (meters / 1000).toFixed(meters < 10_000 ? 1 : 0);
  return `${locale === 'vi' ? km.replace('.', ',') : km} km`;
}

/** Whole minutes and hours of a measured duration, for the `proposal.leg.*` copy. */
export function splitDuration(seconds: number): { hours: number; minutes: number } {
  const total = Math.max(1, Math.round(seconds / 60));
  return { hours: Math.floor(total / 60), minutes: total % 60 };
}

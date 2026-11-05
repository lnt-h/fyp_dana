import type { TFunction } from 'i18next';

import type { City, IsoDate } from '../../lib/api/types';

/** Calendar dates are handled as UTC midnights so no device offset applies (same rule as trips/tripDates.ts). */
export function parseIsoDate(value: IsoDate): Date {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

export function addIsoDays(value: IsoDate, days: number): IsoDate {
  return new Date(parseIsoDate(value).getTime() + days * 86_400_000).toISOString().slice(0, 10);
}

const weekdayKey = (day: number) => `save.date.w${day}` as 'save.date.w0';
const monthKey = (month: number) => `save.date.m${month}` as 'save.date.m0';

/** `16/01/2027` (vi) or `16 Jan 2027` (en). */
export function formatShortDate(t: TFunction, value: IsoDate): string {
  const date = parseIsoDate(value);
  const d = date.getUTCDate();
  return t('save.date.short', { d: String(d), dd: String(d).padStart(2, '0'), month: t(monthKey(date.getUTCMonth())), year: String(date.getUTCFullYear()) });
}

/** `Thứ bảy, 16 tháng 01` (vi) or `Saturday, 16 Jan` (en). */
export function formatLongDate(t: TFunction, value: IsoDate): string {
  const date = parseIsoDate(value);
  return t('save.date.long', { d: String(date.getUTCDate()), n: String(date.getUTCMonth() + 1), month: t(monthKey(date.getUTCMonth())), weekday: t(weekdayKey(date.getUTCDay())) });
}

export function cityName(city: City | null | undefined, isVi: boolean): string {
  if (!city) return '';
  return isVi ? city.name_vi : city.name_en;
}

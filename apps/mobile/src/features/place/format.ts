import type { AppLocale } from '../../i18n';
import type { FactValue, GeoPoint, IsoDate, PlaceFact } from '../../lib/api/types';

/** Days after `verified_at` when a fact or source counts as stale (ASM-008). */
export const STALE_AFTER_DAYS = 180;

const VN_OFFSET_MS = 7 * 60 * 60 * 1000; // Asia/Ho_Chi_Minh has no DST.

/** Today's calendar date in Asia/Ho_Chi_Minh as `YYYY-MM-DD`. */
export function todayInVietnam(now = Date.now()): IsoDate {
  return new Date(now + VN_OFFSET_MS).toISOString().slice(0, 10);
}

/** True when an ISO date is more than 180 days before today (Asia/Ho_Chi_Minh). */
export function isStaleDate(date: IsoDate | null | undefined, now = Date.now()): boolean {
  if (!date) return false;
  const verified = Date.parse(`${date.slice(0, 10)}T00:00:00Z`);
  const today = Date.parse(`${todayInVietnam(now)}T00:00:00Z`);
  if (Number.isNaN(verified)) return false;
  return (today - verified) / 86_400_000 > STALE_AFTER_DAYS;
}

/** A fact is stale when the API says so or its verified date is past the window. */
export const isStaleFact = (fact: PlaceFact) => fact.freshness === 'STALE' || isStaleDate(fact.verified_at);

const monthsEn = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** Calendar date (`YYYY-MM-DD` or a date-time, read in Asia/Ho_Chi_Minh) → `15/09/2026` (vi) or `15 Sep 2026` (en). */
export function formatDate(value: string, locale: AppLocale): string {
  let date = value.slice(0, 10);
  if (value.length > 10) {
    const instant = Date.parse(value);
    if (!Number.isNaN(instant)) date = todayInVietnam(instant);
  }
  const [year, month, day] = date.split('-');
  if (!year || !month || !day) return value;
  return locale === 'vi' ? `${day}/${month}/${year}` : `${Number(day)} ${monthsEn[Number(month) - 1] ?? month} ${year}`;
}

function groupDigits(amount: string, separator: string): string {
  const [whole = '', fraction] = amount.split('.');
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, separator);
  return fraction ? `${grouped}${separator === '.' ? ',' : '.'}${fraction}` : grouped;
}

export function formatMoney(amount: string, currency: string, locale: AppLocale): string {
  if (currency === 'VND') return locale === 'vi' ? `${groupDigits(amount, '.')} ₫` : `${groupDigits(amount, ',')} VND`;
  return `${groupDigits(amount, locale === 'vi' ? '.' : ',')} ${currency}`;
}

export const formatPoint = (point: GeoPoint) => `${point.latitude.toFixed(5)}, ${point.longitude.toFixed(5)}`;

const isObject = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null;

/** Words used inside fact values; the place screen passes its translations (fallbacks for other callers). */
export type FactLabels = {
  free: string;
  child: (price: string) => string;
  /** "Every day" / "Hằng ngày". */
  everyDay?: string;
  /** "Open 24 hours" / "Mở cửa 24/24". */
  allDay?: string;
  /** "Closed Mon" / "Nghỉ T2". */
  closed?: (days: string) => string;
};

const fallbackLabels = (locale: AppLocale): FactLabels => locale === 'vi'
  ? { allDay: 'Mở cửa 24/24', child: price => `trẻ em ${price}`, closed: days => `Nghỉ ${days}`, everyDay: 'Hằng ngày', free: 'Miễn phí' }
  : { allDay: 'Open 24 hours', child: price => `children ${price}`, closed: days => `Closed ${days}`, everyDay: 'Every day', free: 'Free' };

/** ISO weekday 1–7 (Monday first) short names. */
const WEEKDAYS: Record<AppLocale, readonly string[]> = {
  en: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
  vi: ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'],
};

const isTime = (value: unknown): value is string => typeof value === 'string' && /^\d{2}:\d{2}$/.test(value);

/** Intervals of one weekday as `07:30–11:30, 13:30–17:30` (word joiners keep a range on one line); null when closed. */
function dayIntervals(ranges: unknown): string | null {
  if (!Array.isArray(ranges)) return null;
  const parts = ranges.flatMap(range => (Array.isArray(range) && isTime(range[0]) && isTime(range[1]) ? [`${range[0]}\u2060–\u2060${range[1]}`] : []));
  return parts.length ? parts.join(', ') : null;
}

/** Day span label: one day, or `Mon–Fri` for a consecutive run. */
const span = (names: readonly string[], from: number, to: number) => (from === to ? names[from] : `${names[from]}–${names[to]}`);

/**
 * Weekly opening hours (`{weekly: {"1": [["07:30","11:30"], …]}}`, ISO weekdays) → one readable line per locale:
 * "Every day 07:30–11:30, 13:30–17:30", "Tue–Sun 08:00–17:00 · Closed Mon", "Hằng ngày 08:00–17:00". Consecutive days
 * with the same intervals are grouped. Null when no day has a valid interval (the caller then treats hours as unknown).
 */
export function formatWeeklyHours(weekly: unknown, locale: AppLocale, labels: FactLabels = fallbackLabels(locale)): string | null {
  if (!isObject(weekly)) return null;
  const fallback = fallbackLabels(locale);
  const names = WEEKDAYS[locale] ?? WEEKDAYS.en;
  const days = [1, 2, 3, 4, 5, 6, 7].map(day => dayIntervals(weekly[String(day)]));
  if (days.every(day => day === null)) return null;
  if (days.every(day => day === '00:00\u2060–\u206024:00')) return labels.allDay ?? fallback.allDay ?? null;
  if (days.every(day => day === days[0])) return `${labels.everyDay ?? fallback.everyDay} ${days[0]}`;

  const groups: string[] = [];
  const closed: string[] = [];
  for (let start = 0; start < 7;) {
    let end = start;
    while (end + 1 < 7 && days[end + 1] === days[start]) end += 1;
    if (days[start] === null) closed.push(span(names, start, end));
    else groups.push(`${span(names, start, end)} ${days[start]}`);
    start = end + 1;
  }
  const closedLabel = closed.length ? (labels.closed ?? fallback.closed ?? (d => d))(closed.join(', ')) : null;
  return [groups.join('; '), closedLabel].filter(Boolean).join(' · ');
}

/** Renders a KNOWN fact value by its shape (provisional shapes, see types.ts); null when the shape is not recognised. */
export function formatFactValue(value: FactValue | string | null | undefined, locale: AppLocale, labels: FactLabels = fallbackLabels(locale)): string | null {
  if (typeof value === 'string') return value.trim() || null;
  if (!isObject(value)) return null;
  if ('free' in value && value.free === true) return labels.free;
  if ('adult' in value && typeof value.adult === 'number') {
    const currency = typeof value.currency === 'string' ? value.currency : 'VND';
    const adult = formatMoney(String(value.adult), currency, locale);
    return typeof value.child === 'number' ? `${adult} · ${labels.child(formatMoney(String(value.child), currency, locale))}` : adult;
  }
  if ('weekly' in value) return formatWeeklyHours(value.weekly, locale, labels);
  if ('intervals' in value && Array.isArray(value.intervals)) {
    const text = value.intervals.map(interval => `${interval.open} – ${interval.close}`).join(', ');
    return text || null;
  }
  if ('amount' in value && 'currency' in value && typeof value.amount === 'string' && typeof value.currency === 'string') return formatMoney(value.amount, value.currency, locale);
  if ('text' in value && typeof value.text === 'string') return value.text.trim() || null;
  if ('latitude' in value && 'longitude' in value) return formatPoint(value);
  return null;
}

/** Location value of a KNOWN fact, if it carries one. */
export function factPoint(fact: PlaceFact | undefined): GeoPoint | null {
  const value = fact?.knowledge_state === 'KNOWN' ? fact.value : null;
  return isObject(value) && 'latitude' in value && 'longitude' in value ? value : null;
}

/** Days after `fetched_at` when a `WEB_UNVERIFIED` source counts as stale (architecture §5). */
export const WEB_STALE_AFTER_DAYS = 7;

/** True when a web page was fetched more than 7 days ago. Unknown or unparsable dates are not stale. */
export function isWebSourceStale(fetchedAt: string | null | undefined, now = Date.now()): boolean {
  if (!fetchedAt) return false;
  const fetched = Date.parse(fetchedAt);
  if (Number.isNaN(fetched)) return false;
  return (now - fetched) / 86_400_000 > WEB_STALE_AFTER_DAYS;
}

/** Host of a source URL without `www.` (e.g. `vietnam.travel`); null when the URL has no host. */
export function hostOf(url: string | null | undefined): string | null {
  const match = url ? /^[a-z][a-z0-9+.-]*:\/\/(?:[^/?#@]*@)?([^/?#:]+)/i.exec(url.trim()) : null;
  return match ? match[1].toLowerCase().replace(/^www\./, '') : null;
}

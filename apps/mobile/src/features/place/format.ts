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

/** Renders a KNOWN fact value by its shape (provisional shapes, see types.ts); null when the shape is not recognised. */
export function formatFactValue(value: FactValue | string | null | undefined, locale: AppLocale): string | null {
  if (typeof value === 'string') return value.trim() || null;
  if (!isObject(value)) return null;
  if ('intervals' in value && Array.isArray(value.intervals)) {
    const text = value.intervals.map(interval => `${interval.open} – ${interval.close}`).join(', ');
    return text || null;
  }
  if ('amount' in value && 'currency' in value) return formatMoney(value.amount, value.currency, locale);
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

/**
 * Guide data helpers on top of the `/v1` client: a per-scope session cache, full message history (cursor paging) and
 * paged place search for the picker. Questions are never cached or logged; only session ids live here, in memory, for
 * this app session.
 */
import { apiRequest } from '../../lib/api/client';
import { ApiError } from '../../lib/api/errors';
import { createGuideSession } from '../../lib/api/source';
import type { GuideMessage, GuideMessagePage, GuideSession, GuideSessionCreate, Locale, Place, PlaceSummaryPage, Uuid } from '../../lib/api/types';

const enc = encodeURIComponent;
/** API-027 allows up to 50 per page; history follows `next_cursor` up to this many pages. */
const MESSAGE_PAGE = 50;
const MAX_MESSAGE_PAGES = 20;

/** Session id per scope + locale for this app session (memory only). */
const sessions = new Map<string, GuideSession>();

const isExpired = (session: GuideSession) => !!session.expires_at && Date.parse(session.expires_at) <= Date.now() + 30_000;

/** 404 (gone or not ours) or 410 (expired): the cached session cannot be reused. */
export const isSessionGone = (error: unknown) => error instanceof ApiError && (error.status === 404 || error.status === 410);

/** API-027, every page in seq order (cursor paging), so the newest messages are always included. */
export async function listAllGuideMessages(sessionId: Uuid): Promise<GuideMessage[]> {
  const items: GuideMessage[] = [];
  let cursor: string | null = null;
  for (let page = 0; page < MAX_MESSAGE_PAGES; page += 1) {
    const result: GuideMessagePage = await apiRequest<GuideMessagePage>(`/v1/ai/sessions/${enc(sessionId)}/messages`, { query: { cursor, limit: MESSAGE_PAGE } });
    items.push(...result.items);
    cursor = result.next_cursor;
    if (!cursor) break;
  }
  return items;
}

/**
 * Opens the Guide session for a scope: reuses the cached session (and loads its history) until it expires or the
 * server no longer knows it (404/410), then creates a new one (API-024). `fresh` always starts a new session.
 */
export async function openGuideSession(key: string, body: GuideSessionCreate, fresh = false): Promise<{ session: GuideSession; history: GuideMessage[] }> {
  const cacheKey = `${key}:${body.locale}`;
  const cached = fresh ? undefined : sessions.get(cacheKey);
  if (cached && !isExpired(cached)) {
    try {
      return { history: await listAllGuideMessages(cached.id), session: cached };
    } catch (error) {
      if (!isSessionGone(error)) throw error;
    }
  }
  sessions.delete(cacheKey);
  const session = await createGuideSession(body);
  sessions.set(cacheKey, session);
  // A brand-new session has no history; skip the round trip.
  return { history: [], session };
}

/** Drops a cached session (e.g. after "Delete conversation"), so the next open starts fresh. */
export function forgetGuideSession(key: string, locale: Locale): void {
  sessions.delete(`${key}:${locale}`);
}

/**
 * Stored answer for a question whose stream dropped: the newest ASSISTANT message with a seq above the newest
 * TRAVELER message carrying this question. Null when the answer is not stored (yet), so an older answer is never shown.
 */
export function storedAnswerFor(messages: GuideMessage[], question: string): GuideMessage | null {
  const asked = [...messages].reverse().find(message => message.role === 'TRAVELER' && message.content.trim() === question.trim());
  if (!asked) return null;
  const answers = messages.filter(message => message.role === 'ASSISTANT' && message.seq > asked.seq);
  return answers.length ? answers.reduce((latest, message) => (message.seq > latest.seq ? message : latest)) : null;
}

const PLACE_PAGE = 30;

/** API-010 one page of the city's places (name sort; `q` searches), with the cursor for the next page. */
export async function searchPlacesPage(cityId: Uuid, locale: Locale, q: string, cursor: string | null): Promise<{ items: Place[]; next: string | null }> {
  const query = q.trim();
  const page = await apiRequest<PlaceSummaryPage>('/v1/places', {
    query: { city_id: cityId, cursor, limit: PLACE_PAGE, locale, q: query || undefined, sort: query ? 'relevance' : 'name' },
  });
  return { items: page.items, next: page.next_cursor };
}

/** The city's published places (all pages, name order), cached per city + locale for this app session. */
const cityPlaces = new Map<string, Promise<Place[]>>();

export function loadCityPlaces(cityId: Uuid, locale: Locale): Promise<Place[]> {
  const key = `${cityId}:${locale}`;
  let pending = cityPlaces.get(key);
  if (!pending) {
    pending = (async () => {
      const all: Place[] = [];
      let cursor: string | null = null;
      for (let page = 0; page < 10; page += 1) {
        const result = await searchPlacesPage(cityId, locale, '', cursor);
        all.push(...result.items);
        cursor = result.next;
        if (!cursor) break;
      }
      return all;
    })();
    pending.catch(() => cityPlaces.delete(key));
    cityPlaces.set(key, pending);
  }
  return pending;
}

const fold = (value: string) => value.normalize('NFC').toLocaleLowerCase();

/**
 * Published places an answer names (catalog name or Vietnamese name appears in the text), in order of first mention.
 * Deterministic text match against the catalog only: the card links to a published place, never to a model guess.
 */
export function placesMentioned(text: string, places: Place[], excludeId?: string | null, max = 3): Place[] {
  const haystack = fold(text);
  const hits: { place: Place; at: number }[] = [];
  for (const place of places) {
    if (place.id === excludeId) continue;
    const names = [place.name, place.name_vi].filter((name): name is string => !!name && name.trim().length >= 5);
    const at = Math.min(...names.map(name => haystack.indexOf(fold(name))).filter(index => index >= 0));
    if (Number.isFinite(at)) hits.push({ at, place });
  }
  return hits.sort((a, b) => a.at - b.at).slice(0, max).map(hit => hit.place);
}

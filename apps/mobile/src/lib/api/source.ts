/**
 * Data source for the UI. Remote vs fixture is decided once by `isRemoteEnabled()` (config.ts): with
 * `EXPO_PUBLIC_API_URL` set, calls go to the Gonarra API through `client.ts`/`streams.ts`; otherwise every call is
 * served from local fixture data (src/lib/api/fixtures, Đà Nẵng only, not catalog data).
 */
import { currentLocale } from '../../i18n';
import { apiRequest, newRequestId } from './client';
import { isRemoteEnabled } from './config';
import { ApiError } from './errors';
import {
  FIXTURE_PREVIEW_ID,
  FIXTURE_PREVIEW_ROUTE_UNAVAILABLE_ID,
  fixtureCategories,
  fixtureCities,
  fixtureGuideMessages,
  fixtureGuideSession,
  fixturePlaceCard,
  fixturePlaceDetail,
  fixturePlaces,
  fixturePreferences,
  fixturePreview,
  fixtureTripDetail,
  fixtureTrips,
  guideAnswer,
  guideInsufficientEvidence,
} from './fixtures/da-nang';
import { runGuideStream, runPlanningStream } from './streams';
import type {
  Category,
  City,
  GuideMessage,
  GuideMessagePage,
  GuideQuestion,
  GuideSession,
  GuideSessionCreate,
  GuideStage,
  GuideStreamEvent,
  Identity,
  Place,
  PlaceCard,
  PlaceDetail,
  PlaceSummaryPage,
  PlanPreview,
  PlanPreviewCreate,
  PlanningStage,
  PlanningStreamEvent,
  Preferences,
  Trip,
  TripCreate,
  TripDetail,
  TripPage,
  Uuid,
} from './types';

export { ApiError } from './errors';
export { isRemoteEnabled } from './config';

/** True when calls are served from fixtures (no `EXPO_PUBLIC_API_URL`). Kept for the dev-only fixture controls. */
export const useFixtures = !isRemoteEnabled();

/** A fresh `Idempotency-Key` (UUID); reuse the same key when retrying the same request. */
export const newIdempotencyKey = (): string => newRequestId();

/** Resolves after `ms`; resolves `false` early if the signal aborts. */
function wait(ms: number, signal?: AbortSignal): Promise<boolean> {
  return new Promise(resolve => {
    if (signal?.aborted) { resolve(false); return; }
    const timer = setTimeout(() => { signal?.removeEventListener('abort', onAbort); resolve(true); }, ms);
    function onAbort() { clearTimeout(timer); resolve(false); }
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

const notFound = () => new ApiError({ code: 'resource_not_found', message: 'This item was not found', retryable: false }, 404);

const enc = encodeURIComponent;

/** API-003 `GET /v1/me`: the internal account id for the Clerk session. Fixture: a fake identity. */
export async function getMe(): Promise<Identity> {
  if (isRemoteEnabled()) return apiRequest<Identity>('/v1/me');
  await wait(100);
  return { account_id: '00000000-0000-4000-8000-000000000a01', session_id: null, subject: 'fixture-user' };
}

/** API-008 `GET /v1/cities` (enabled cities; Đà Nẵng only for the FYP release). */
export async function listCities(): Promise<City[]> {
  if (isRemoteEnabled()) return (await apiRequest<{ items: City[] }>('/v1/cities', { query: { locale: currentLocale() } })).items;
  await wait(150);
  return fixtureCities;
}

/** API-009 `GET /v1/categories`. */
export async function listCategories(): Promise<Category[]> {
  if (isRemoteEnabled()) return (await apiRequest<{ items: Category[] }>('/v1/categories')).items;
  await wait(150);
  return fixtureCategories;
}

/** Page size for place search; the UI shows one page (cursor paging is not wired yet). */
const PLACE_PAGE_LIMIT = 50;

/** API-010 `GET /v1/places?city_id&q&category_code` (first page only). Fixture: Đà Nẵng places; other cities return none. */
export async function searchPlaces(cityId: Uuid, q?: string, categoryCode?: string | null): Promise<Place[]> {
  if (isRemoteEnabled()) {
    const query = { category_code: categoryCode ?? undefined, city_id: cityId, limit: PLACE_PAGE_LIMIT, locale: currentLocale(), q: q?.trim() || undefined };
    return (await apiRequest<PlaceSummaryPage>('/v1/places', { query })).items;
  }
  await wait(300);
  return fixturePlaces(currentLocale(), q)
    .filter(place => place.city_id === cityId)
    .filter(place => !categoryCode || place.category_code === categoryCode);
}

/** API-011 `GET /v1/places/{place_id}`. */
export async function getPlace(placeId: Uuid): Promise<PlaceDetail> {
  if (isRemoteEnabled()) return apiRequest<PlaceDetail>(`/v1/places/${enc(placeId)}`, { query: { locale: currentLocale() } });
  await wait(250);
  const place = fixturePlaceDetail(placeId, currentLocale());
  if (!place) throw notFound();
  return place;
}

/** API-017 `GET /v1/trips/{trip_id}/stops/{stop_id}/place-card`. */
export async function getPlaceCard(tripId: Uuid, stopId: Uuid): Promise<PlaceCard> {
  if (isRemoteEnabled()) return apiRequest<PlaceCard>(`/v1/trips/${enc(tripId)}/stops/${enc(stopId)}/place-card`);
  await wait(400);
  const card = fixturePlaceCard(stopId);
  if (!card) throw notFound();
  return card;
}

/** API-012 `POST /v1/trips` (fixture: returns the fixture trip as a new DRAFT at revision 0). */
export async function createTrip(input: TripCreate): Promise<Trip> {
  if (isRemoteEnabled()) return apiRequest<Trip>('/v1/trips', { body: input, idempotencyKey: newIdempotencyKey(), method: 'POST' });
  await wait(250);
  return { ...fixtureTrips[0], ...input, revision: 0, saved_at: null, status: 'DRAFT' };
}

/** API-004 `GET /v1/me/preferences`. */
export async function getPreferences(): Promise<Preferences> {
  if (isRemoteEnabled()) return apiRequest<Preferences>('/v1/me/preferences');
  await wait(150);
  return fixturePreferences(currentLocale());
}

/** API-014 `GET /v1/trips/{trip_id}`. */
export async function getTrip(tripId: Uuid): Promise<TripDetail> {
  if (isRemoteEnabled()) return apiRequest<TripDetail>(`/v1/trips/${enc(tripId)}`, { query: { locale: currentLocale() } });
  await wait(250);
  const trip = fixtureTripDetail(tripId, currentLocale());
  if (!trip) throw notFound();
  return trip;
}

/** API-024 `POST /v1/ai/sessions`, `scope` CITY (+ `city_code`) or PLACE (+ `place_id`). Fixture: the Chùa Cầu session's history whatever the scope. */
export async function createGuideSession(input: GuideSessionCreate): Promise<GuideSession> {
  if (isRemoteEnabled()) return apiRequest<GuideSession>('/v1/ai/sessions', { body: input, method: 'POST' });
  await wait(200);
  const session = fixtureGuideSession(input.locale);
  return input.scope === 'CITY'
    ? { ...session, city_code: input.city_code, place_id: null, scope: 'CITY', trip_id: input.trip_id ?? null }
    : { ...session, place_id: input.place_id, scope: 'PLACE', trip_id: input.trip_id ?? null };
}

/** API-027 `GET /v1/ai/sessions/{session_id}/messages` (first page, ordered by seq). */
export async function listGuideMessages(sessionId: Uuid): Promise<GuideMessage[]> {
  if (isRemoteEnabled()) return (await apiRequest<GuideMessagePage>(`/v1/ai/sessions/${enc(sessionId)}/messages`, { query: { limit: 50 } })).items;
  await wait(250);
  return fixtureGuideMessages(currentLocale());
}

/** API-019 `getPlanPreview`: `GET /v1/plan-previews/{preview_id}`. */
export async function getPreview(id: Uuid): Promise<PlanPreview> {
  if (isRemoteEnabled()) return apiRequest<PlanPreview>(`/v1/plan-previews/${enc(id)}`, { query: { locale: currentLocale() } });
  await wait(250);
  if (id === FIXTURE_PREVIEW_ID) return fixturePreview(currentLocale());
  if (id === FIXTURE_PREVIEW_ROUTE_UNAVAILABLE_ID) return fixturePreview(currentLocale(), 'routeUnavailable');
  throw notFound();
}

/** API-013 `listTrips`: `GET /v1/trips?status=SAVED` (saved trips, newest first; first page). */
export async function listTrips(): Promise<Trip[]> {
  if (isRemoteEnabled()) return (await apiRequest<TripPage>('/v1/trips', { query: { limit: 50, status: 'SAVED' } })).items;
  await wait(250);
  return fixtureTrips;
}

/** Fixture planning run: the catalog-first path (no research stages). */
const fixturePlanningStages: PlanningStage[] = ['VALIDATING_REQUEST', 'SELECTING_PLACES', 'ROUTING', 'SCHEDULING', 'CHECKING_HEALTH', 'WRITING'];

/**
 * API-018 planning stream: `POST /v1/trips/{trip_id}/plan-previews` with `Accept: text/event-stream` and a fresh
 * `Idempotency-Key`. Events: `progress` (stages), then one terminal `preview_ready`, `clarification_required` or
 * `error`. Fixture: the stages ~700 ms apart, then `preview_ready`. Stops quietly on abort.
 */
export async function streamPlanning(tripId: Uuid, input: PlanPreviewCreate, onEvent: (event: PlanningStreamEvent) => void, signal?: AbortSignal): Promise<void> {
  if (isRemoteEnabled()) {
    return runPlanningStream(`/v1/trips/${enc(tripId)}/plan-previews`, { body: input, idempotencyKey: newIdempotencyKey(), method: 'POST', signal }, onEvent);
  }
  for (const stage of fixturePlanningStages) {
    if (!(await wait(700, signal))) return;
    onEvent({ stage, type: 'progress' });
  }
  if (!(await wait(700, signal))) return;
  onEvent({ plan_health: 'WARNING', preview_id: FIXTURE_PREVIEW_ID, preview_revision: 1, type: 'preview_ready' });
}

/** Fixture rule: questions about parking or prices have no supporting evidence in the sample sources. */
const unsupportedQuestion = /park|price|đỗ xe|gửi xe|giá/i;

const fixtureGuideStages: GuideStage[] = ['VALIDATING', 'RETRIEVING', 'ANSWERING'];

/**
 * API-028 Guide stream: `POST /v1/ai/sessions/{session_id}/messages` with `Accept: text/event-stream`. Events:
 * `progress`, `text` deltas, then terminal `result` (stored message) or `error`. Fixture: stages, word deltas, then
 * the stored `result` message. Stops quietly on abort.
 */
export async function streamGuide(sessionId: Uuid, question: GuideQuestion, onEvent: (event: GuideStreamEvent) => void, signal?: AbortSignal): Promise<void> {
  if (isRemoteEnabled()) {
    return runGuideStream(`/v1/ai/sessions/${enc(sessionId)}/messages`, { body: question, idempotencyKey: newIdempotencyKey(), method: 'POST', signal }, onEvent);
  }
  const locale = currentLocale();
  const message = unsupportedQuestion.test(question.content) ? guideInsufficientEvidence(locale) : guideAnswer(locale);
  for (const stage of fixtureGuideStages) {
    if (!(await wait(500, signal))) return;
    onEvent({ stage, type: 'progress' });
  }
  for (const word of message.content.split(/(?<=\s)/)) {
    if (!(await wait(60, signal))) return;
    onEvent({ delta: word, type: 'text' });
  }
  onEvent({ message, type: 'result' });
}

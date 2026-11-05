/**
 * Data source for the UI. With EXPO_PUBLIC_USE_FIXTURES=1 every call is served from local fixture data
 * (src/lib/api/fixtures, not catalog data); otherwise calls throw until the API client lands (TASK-001).
 */
import { currentLocale } from '../../i18n';
import {
  HOI_AN_PREVIEW_ID,
  HOI_AN_PREVIEW_ROUTE_UNAVAILABLE_ID,
  fixtureCategories,
  fixtureCities,
  fixtureGuideMessages,
  fixtureGuideSession,
  fixturePlaceCard,
  fixturePlaceDetail,
  fixturePlaces,
  fixturePreferences,
  fixtureTripDetail,
  fixtureTrips,
  guideAnswer,
  guideInsufficientEvidence,
  hoiAnPreview,
} from './fixtures/hoi-an';
import type {
  Category,
  City,
  ErrorDetail,
  GuideMessage,
  GuideQuestion,
  GuideSession,
  GuideSessionCreate,
  GuideStreamEvent,
  Place,
  PlaceCard,
  PlaceDetail,
  PlanPreview,
  PlanPreviewCreate,
  PlanningStage,
  PlanningStreamEvent,
  Preferences,
  Trip,
  TripCreate,
  TripDetail,
  Uuid,
} from './types';

/**
 * Fixture data is used when EXPO_PUBLIC_USE_FIXTURES=1, and by default in development builds until the API client is
 * wired (TASK-001): no EXPO_PUBLIC_API_URL means there is no server to call. Set EXPO_PUBLIC_USE_FIXTURES=0 to force
 * the real API path.
 */
const fixtureFlag = process.env.EXPO_PUBLIC_USE_FIXTURES;
export const useFixtures = fixtureFlag === '1' || (fixtureFlag !== '0' && __DEV__ && !process.env.EXPO_PUBLIC_API_URL);

function notWired(): never {
  throw new Error('API not wired yet (TASK-001)');
}

/** Resolves after `ms`; resolves `false` early if the signal aborts. */
function wait(ms: number, signal?: AbortSignal): Promise<boolean> {
  return new Promise(resolve => {
    if (signal?.aborted) { resolve(false); return; }
    const timer = setTimeout(() => { signal?.removeEventListener('abort', onAbort); resolve(true); }, ms);
    function onAbort() { clearTimeout(timer); resolve(false); }
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

/** Thrown for a non-2xx response; `error` is the Gonarra envelope body (map `error.code` to copy, S-1). */
export class ApiError extends Error {
  constructor(public readonly error: ErrorDetail, public readonly status: number) {
    super(error.code);
  }
}

const notFound = () => new ApiError({ code: 'not_found', message: 'This item was not found', retryable: false }, 404);

/** `GET /v1/cities`. */
export async function listCities(): Promise<City[]> {
  if (!useFixtures) notWired();
  await wait(150);
  return fixtureCities;
}

/** `GET /v1/categories`. */
export async function listCategories(): Promise<Category[]> {
  if (!useFixtures) notWired();
  await wait(150);
  return fixtureCategories;
}

/** `GET /v1/places?city_id&q` (fixture: Hội An only; other cities return no items). */
export async function searchPlaces(cityId: Uuid, q?: string): Promise<Place[]> {
  if (!useFixtures) notWired();
  await wait(300);
  return fixturePlaces(currentLocale(), q).filter(place => place.city_id === cityId);
}

/** `GET /v1/places/{place_id}`. */
export async function getPlace(placeId: Uuid): Promise<PlaceDetail> {
  if (!useFixtures) notWired();
  await wait(250);
  const place = fixturePlaceDetail(placeId, currentLocale());
  if (!place) throw notFound();
  return place;
}

/** `GET /v1/trips/{trip_id}/stops/{stop_id}/place-card`. */
export async function getPlaceCard(_tripId: Uuid, stopId: Uuid): Promise<PlaceCard> {
  if (!useFixtures) notWired();
  await wait(400);
  const card = fixturePlaceCard(stopId);
  if (!card) throw notFound();
  return card;
}

/** `POST /v1/trips` (fixture: returns the Hội An trip as a new DRAFT at revision 0). */
export async function createTrip(input: TripCreate): Promise<Trip> {
  if (!useFixtures) notWired();
  await wait(250);
  return { ...fixtureTrips[0], ...input, revision: 0, saved_at: null, status: 'DRAFT' };
}

/** `GET /v1/me/preferences`. */
export async function getPreferences(): Promise<Preferences> {
  if (!useFixtures) notWired();
  await wait(150);
  return fixturePreferences(currentLocale());
}

/** `GET /v1/trips/{trip_id}`. */
export async function getTrip(tripId: Uuid): Promise<TripDetail> {
  if (!useFixtures) notWired();
  await wait(250);
  const trip = fixtureTripDetail(tripId, currentLocale());
  if (!trip) throw notFound();
  return trip;
}

/** `POST /v1/ai/sessions` (fixture: always the Chùa Cầu session, whatever place is passed). */
export async function createGuideSession(input: GuideSessionCreate): Promise<GuideSession> {
  if (!useFixtures) notWired();
  await wait(200);
  return { ...fixtureGuideSession(input.locale), place_id: input.place_id, trip_id: input.trip_id ?? null };
}

/** `GET /v1/ai/sessions/{session_id}/messages`. */
export async function listGuideMessages(_sessionId: Uuid): Promise<GuideMessage[]> {
  if (!useFixtures) notWired();
  await wait(250);
  return fixtureGuideMessages(currentLocale());
}

/** `getPlanPreview`: `GET /v1/plan-previews/{preview_id}`. */
export async function getPreview(id: Uuid): Promise<PlanPreview> {
  if (!useFixtures) notWired();
  await wait(250);
  if (id === HOI_AN_PREVIEW_ID) return hoiAnPreview(currentLocale());
  if (id === HOI_AN_PREVIEW_ROUTE_UNAVAILABLE_ID) return hoiAnPreview(currentLocale(), 'routeUnavailable');
  throw notFound();
}

/** `listTrips`: `GET /v1/trips` (saved trips, newest first). */
export async function listTrips(): Promise<Trip[]> {
  if (!useFixtures) notWired();
  await wait(250);
  return fixtureTrips;
}

const planningStages: PlanningStage[] = ['VALIDATING_REQUEST', 'SELECTING_PLACES', 'ROUTING', 'SCHEDULING', 'CHECKING_HEALTH'];

/** Planning SSE stream (`POST /v1/trips/{trip_id}/plan-previews`; trip id added when the API is wired). Fixture: the five progress stages ~700 ms apart, then `preview_ready`. Stops quietly on abort. */
export async function streamPlanning(_input: PlanPreviewCreate, onEvent: (event: PlanningStreamEvent) => void, signal?: AbortSignal): Promise<void> {
  if (!useFixtures) notWired();
  for (const stage of planningStages) {
    if (!(await wait(700, signal))) return;
    onEvent({ stage, type: 'progress' });
  }
  if (!(await wait(700, signal))) return;
  onEvent({ plan_health: 'WARNING', preview_id: HOI_AN_PREVIEW_ID, preview_revision: 1, type: 'preview_ready' });
}

/** Fixture rule: questions about parking or prices have no supporting evidence in the sample sources. */
const unsupportedQuestion = /park|price|đỗ xe|gửi xe|giá/i;

/** Guide SSE stream (`POST /v1/ai/sessions/{session_id}/messages`; session id added when the API is wired). Fixture: progress stages, text deltas, then the stored `result` message. Stops quietly on abort. */
export async function streamGuide(question: GuideQuestion, onEvent: (event: GuideStreamEvent) => void, signal?: AbortSignal): Promise<void> {
  if (!useFixtures) notWired();
  const locale = currentLocale();
  const message = unsupportedQuestion.test(question.content) ? guideInsufficientEvidence(locale) : guideAnswer(locale);
  for (const stage of ['RETRIEVING', 'ANSWERING'] as const) {
    if (!(await wait(500, signal))) return;
    onEvent({ stage, type: 'progress' });
  }
  for (const word of message.content.split(/(?<=\s)/)) {
    if (!(await wait(60, signal))) return;
    onEvent({ delta: word, type: 'text' });
  }
  onEvent({ message, type: 'result' });
}

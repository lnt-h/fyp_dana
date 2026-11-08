/**
 * Data source for the UI: every call goes to the Gonarra `/v1` API (`EXPO_PUBLIC_API_URL`, required; see config.ts)
 * through `client.ts`/`streams.ts` with the Clerk session token. There is no local or demo data.
 */
import { currentLocale } from '../../i18n';
import { apiRequest, newRequestId } from './client';
import { runGuideStream, runPlanningStream } from './streams';
import type {
  Category,
  City,
  GuideMessage,
  GuideMessagePage,
  GuideQuestion,
  GuideSession,
  GuideSessionCreate,
  GuideStreamEvent,
  Identity,
  Place,
  PlaceCard,
  PlaceDetail,
  PlaceSummaryPage,
  PlanPreview,
  PlanPreviewCreate,
  PlanningStreamEvent,
  Preferences,
  Trip,
  TripCreate,
  TripDetail,
  TripPage,
  Uuid,
} from './types';

export { ApiError, loadErrorKind, type LoadErrorKind } from './errors';
export { isApiConfigured } from './config';

/** A fresh `Idempotency-Key` (UUID); reuse the same key when retrying the same request. */
export const newIdempotencyKey = (): string => newRequestId();

const enc = encodeURIComponent;

/** API-003 `GET /v1/me`: the internal account id for the Clerk session. */
export async function getMe(): Promise<Identity> {
  return apiRequest<Identity>('/v1/me');
}

/** API-008 `GET /v1/cities` (enabled cities; Đà Nẵng only for the FYP release). */
export async function listCities(): Promise<City[]> {
  return (await apiRequest<{ items: City[] }>('/v1/cities', { query: { locale: currentLocale() } })).items;
}

/** API-009 `GET /v1/categories`. */
export async function listCategories(): Promise<Category[]> {
  return (await apiRequest<{ items: Category[] }>('/v1/categories')).items;
}

/** Page size for place search; the UI shows one page (cursor paging is not wired yet). */
const PLACE_PAGE_LIMIT = 50;

/** API-010 `GET /v1/places?city_id&q&category_code` (first page only). */
export async function searchPlaces(cityId: Uuid, q?: string, categoryCode?: string | null, areaCode?: string | null): Promise<Place[]> {
  const query = {
    area_code: areaCode ?? undefined, category_code: categoryCode ?? undefined, city_id: cityId, limit: PLACE_PAGE_LIMIT, locale: currentLocale(),
    q: q?.trim() || undefined,
  };
  return (await apiRequest<PlaceSummaryPage>('/v1/places', { query })).items;
}

/** API-011 `GET /v1/places/{place_id}`. */
export async function getPlace(placeId: Uuid): Promise<PlaceDetail> {
  return apiRequest<PlaceDetail>(`/v1/places/${enc(placeId)}`, { query: { locale: currentLocale() } });
}

/** API-017 `GET /v1/trips/{trip_id}/stops/{stop_id}/place-card`. */
export async function getPlaceCard(tripId: Uuid, stopId: Uuid): Promise<PlaceCard> {
  return apiRequest<PlaceCard>(`/v1/trips/${enc(tripId)}/stops/${enc(stopId)}/place-card`);
}

/** API-012 `POST /v1/trips`. */
export async function createTrip(input: TripCreate): Promise<Trip> {
  return apiRequest<Trip>('/v1/trips', { body: input, idempotencyKey: newIdempotencyKey(), method: 'POST' });
}

/** API-004 `GET /v1/me/preferences`. */
export async function getPreferences(): Promise<Preferences> {
  return apiRequest<Preferences>('/v1/me/preferences');
}

/** API-014 `GET /v1/trips/{trip_id}`. */
export async function getTrip(tripId: Uuid): Promise<TripDetail> {
  return apiRequest<TripDetail>(`/v1/trips/${enc(tripId)}`, { query: { locale: currentLocale() } });
}

/** API-024 `POST /v1/ai/sessions`, `scope` CITY (+ `city_code`) or PLACE (+ `place_id`). */
export async function createGuideSession(input: GuideSessionCreate): Promise<GuideSession> {
  return apiRequest<GuideSession>('/v1/ai/sessions', { body: input, method: 'POST' });
}

/** API-027 `GET /v1/ai/sessions/{session_id}/messages` (first page, ordered by seq). */
export async function listGuideMessages(sessionId: Uuid): Promise<GuideMessage[]> {
  return (await apiRequest<GuideMessagePage>(`/v1/ai/sessions/${enc(sessionId)}/messages`, { query: { limit: 50 } })).items;
}

/** API-019 `getPlanPreview`: `GET /v1/plan-previews/{preview_id}`. */
export async function getPreview(id: Uuid): Promise<PlanPreview> {
  return apiRequest<PlanPreview>(`/v1/plan-previews/${enc(id)}`, { query: { locale: currentLocale() } });
}

/** API-013 `listTrips`: `GET /v1/trips?status=SAVED` (saved trips, newest first; first page). */
export async function listTrips(): Promise<Trip[]> {
  return (await apiRequest<TripPage>('/v1/trips', { query: { limit: 50, status: 'SAVED' } })).items;
}

/**
 * API-018 planning stream: `POST /v1/trips/{trip_id}/plan-previews` with `Accept: text/event-stream` and a fresh
 * `Idempotency-Key`. Events: `progress` (stages), then one terminal `preview_ready`, `clarification_required` or
 * `error`. Stops quietly on abort.
 */
export async function streamPlanning(tripId: Uuid, input: PlanPreviewCreate, onEvent: (event: PlanningStreamEvent) => void, signal?: AbortSignal): Promise<void> {
  return runPlanningStream(`/v1/trips/${enc(tripId)}/plan-previews`, { body: input, idempotencyKey: newIdempotencyKey(), method: 'POST', signal }, onEvent);
}

/**
 * API-028 Guide stream: `POST /v1/ai/sessions/{session_id}/messages` with `Accept: text/event-stream`. Events:
 * `progress`, `text` deltas, then terminal `result` (stored message) or `error`. Stops quietly on abort.
 */
export async function streamGuide(sessionId: Uuid, question: GuideQuestion, onEvent: (event: GuideStreamEvent) => void, signal?: AbortSignal): Promise<void> {
  return runGuideStream(`/v1/ai/sessions/${enc(sessionId)}/messages`, { body: question, idempotencyKey: newIdempotencyKey(), method: 'POST', signal }, onEvent);
}

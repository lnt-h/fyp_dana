/**
 * Proposal editing data source: API-019 head read, API-020 `editPlanPreview`, API-021 `regeneratePlanDay`, and the
 * SCR-028 picker search (API-010 with `category_code`). Always the Gonarra `/v1` API (see config.ts).
 *
 * The client never computes times, distances, durations or Plan Health: it sends an op list (`edits[]`) and renders
 * whatever revision comes back.
 */
import { currentLocale } from '../../i18n';
import { apiRequest } from './client';
import { getPreview, newIdempotencyKey as freshIdempotencyKey, searchPlaces } from './source';
import { runPlanningStream } from './streams';
import type { Locale, Place, PlanPreview, PlanningStreamEvent, TravelMode, Uuid } from './types';

/* ---------------------------------------------------------------- Contract mirror (openapi.yaml) */

/** `PreviewEditOperation`, narrowed per `op` (the contract has one flat object with optional fields). */
export type PreviewEditOperation =
  | { op: 'MOVE_STOP'; stop_id: Uuid; day_index: number; to_ordinal: number }
  | { op: 'ADD_STOP'; day_index: number; place_id: Uuid; to_ordinal?: number }
  | { op: 'REMOVE_STOP'; stop_id: Uuid }
  | { op: 'REPLACE_STOP'; stop_id: Uuid; place_id: Uuid }
  | { op: 'SET_VISIT_MINUTES'; stop_id: Uuid; visit_minutes: number }
  | { op: 'SET_LEG_MODE'; from_stop_id: Uuid; to_stop_id: Uuid; travel_mode: TravelMode }
  | { op: 'LOCK_STOP'; stop_id: Uuid }
  | { op: 'UNLOCK_STOP'; stop_id: Uuid };

/** `PlanPreviewEdit` (API-020 body): 1–20 ops applied in order to `expected_revision`. */
export type PlanPreviewEdit = { expected_revision: number; edits: PreviewEditOperation[] };

/** `RegenerateDayRequest` (API-021 body). */
export type RegenerateDayRequest = {
  expected_revision: number;
  day_index: 1 | 2 | 3;
  locked_stop_ids?: Uuid[];
  instruction?: string | null;
  locale?: Locale;
};

export const MAX_EDITS_PER_REQUEST = 20;
export const MAX_STOPS_PER_DAY = 20;

/** A fresh `Idempotency-Key`; reuse the same key when retrying the same request. */
export function newIdempotencyKey(): string {
  return freshIdempotencyKey();
}

/* ---------------------------------------------------------------- Public calls */

/** API-019 `GET /v1/plan-previews/{preview_id}`: the head revision. */
export async function getPreviewHead(previewId: Uuid): Promise<PlanPreview> {
  return getPreview(previewId);
}

/**
 * API-020 `PATCH /v1/plan-previews/{preview_id}` with `Idempotency-Key`. Resolves with the new head revision; rejects
 * with `ApiError` (409 `revision_conflict`, 410, 422, 503 `route_unavailable`) or a network `TypeError`.
 */
export async function editPreview(previewId: Uuid, body: PlanPreviewEdit, idempotencyKey: string): Promise<PlanPreview> {
  return apiRequest<PlanPreview>(`/v1/plan-previews/${encodeURIComponent(previewId)}`, { body, idempotencyKey, method: 'PATCH', query: { locale: currentLocale() } });
}

/**
 * API-021 `POST /v1/plan-previews/{preview_id}/regenerate` in stream mode (`Accept: text/event-stream`): progress
 * stages, then `preview_ready` (read the new head with `getPreviewHead`) or `error`. Stops quietly on abort.
 */
export async function streamRegenerateDay(
  previewId: Uuid,
  body: RegenerateDayRequest,
  idempotencyKey: string,
  onEvent: (event: PlanningStreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  return runPlanningStream(
    `/v1/plan-previews/${encodeURIComponent(previewId)}/regenerate`,
    { body, idempotencyKey, method: 'POST', query: { locale: currentLocale() }, signal },
    onEvent,
  );
}

/** API-010 `GET /v1/places?city_id&q&category_code` (published places of the trip's city only). */
export async function searchCityPlaces(cityId: Uuid, q?: string, categoryCode?: string | null): Promise<Place[]> {
  const items = await searchPlaces(cityId, q, categoryCode);
  items.forEach(place => placeCache.set(place.id, place));
  return items;
}

/** A place seen in a recent picker search (display only: photo, category). */
export function cachedPlace(placeId: Uuid): Place | undefined {
  return placeCache.get(placeId);
}

const placeCache = new Map<Uuid, Place>();

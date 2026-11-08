/**
 * Save, booking handoff and trip deletion calls (SCR-029, SCR-037, SCR-031). Always the Gonarra `/v1` API (see
 * config.ts); no local or demo data.
 */
import { currentLocale } from '../../i18n';
import { apiRequest, apiRequestRaw } from './client';
import { ApiError } from './errors';
import type { AcceptPreviewRequest, HandoffKind, HandoffLink, StayPricePage, TripDetail, Uuid } from './types';

/* ---------------------------------------------------------------- Contract mirrors */

export type { AcceptPreviewRequest, StayPrice, StayPricePage } from './types';

/** API-022 200 body plus the `Idempotent-Replayed` header (true when the server returned the original response). */
export type AcceptPreviewResult = {
  trip: TripDetail;
  replayed: boolean;
};

/**
 * Thrown when no response arrived (connection lost mid-request). The save may or may not have completed server-side,
 * so a retry must reuse the same `Idempotency-Key` (S-1 "Network failure").
 */
export class NetworkError extends Error {
  constructor() {
    super('network_failure');
  }
}

/** `EXPO_PUBLIC_FEATURE_PRICES=1` turns on the Could-priority indicative price section (FEATURE_STAY_PRICES, S-5). */
export const stayPricesEnabled = process.env.EXPO_PUBLIC_FEATURE_PRICES === '1';

/* ---------------------------------------------------------------- Calls */

/**
 * API-022 `POST /v1/plan-previews/{preview_id}/accept` with a required `Idempotency-Key`. Replaying the same key and
 * body returns the original trip with `replayed: true`; the same key with a different body is 409
 * `idempotency_key_reused`. Errors: 409 `plan_blocked` (`context.reasons`), 409 `revision_conflict`
 * (`context.current_revision`), 410 `preview_expired`/`preview_closed`, 422 `web_unverified_acknowledgement_required`
 * (plan has a WEB_UNVERIFIED stop and `acknowledge_web_unverified` is false, OQ-128), `NetworkError` when no response
 * arrived.
 */
export async function acceptPreview(previewId: Uuid, body: AcceptPreviewRequest, idempotencyKey: string): Promise<AcceptPreviewResult> {
  try {
    const response = await apiRequestRaw<TripDetail>(`/v1/plan-previews/${encodeURIComponent(previewId)}/accept`, { body, idempotencyKey, method: 'POST' });
    return { replayed: response.headers.get('Idempotent-Replayed') === 'true', trip: response.data };
  } catch (error) {
    // No response: the save may have committed; the caller retries with the same key.
    if (error instanceof TypeError) throw new NetworkError();
    throw error;
  }
}

/** STAY partners requested via the API-030 `partner` query (contract 1.0). */
const STAY_PARTNERS = ['agoda', 'booking_com'] as const;

/**
 * API-030 `GET /v1/trips/{trip_id}/handoff-links?kind[&partner][&stop_id]`, one request per kind and, for STAY, one per
 * partner (`agoda`, `booking_com`). The contract 200 body is a single `HandoffLink`. Requires a SAVED trip (409
 * `trip_not_saved`).
 */
export async function getHandoffLinks(tripId: Uuid, options: { kinds?: HandoffKind[]; stopId?: Uuid } = {}): Promise<HandoffLink[]> {
  const kinds = options.kinds ?? ['STAY', 'ACTIVITY', 'TRANSPORT'];
  // One request per (kind, partner): STAY has two partners selected with `partner` (agoda is the server default).
  const requests = kinds.flatMap(kind => (kind === 'STAY' ? STAY_PARTNERS : [undefined]).map(partner => ({ kind, partner })));
  return Promise.all(requests.map(({ kind, partner }) => apiRequest<HandoffLink>(`/v1/trips/${encodeURIComponent(tripId)}/handoff-links`, {
    query: { kind, locale: currentLocale(), partner, stop_id: options.stopId },
  })));
}

/**
 * API-031 `GET /v1/trips/{trip_id}/stay-prices` (Could, behind FEATURE_STAY_PRICES). `Cache-Control: no-store`: keep the
 * result in component state only; never cache, persist or attach it to a trip. When the flag is off this is 503
 * `feature_disabled` and callers should not reach it.
 */
export async function getStayPrices(tripId: Uuid): Promise<StayPricePage> {
  if (!stayPricesEnabled) {
    throw new ApiError({ code: 'feature_disabled', message: 'Feature disabled', retryable: false }, 503);
  }
  return apiRequest<StayPricePage>(`/v1/trips/${encodeURIComponent(tripId)}/stay-prices`);
}

/** API-016 `DELETE /v1/trips/{trip_id}`. 204 and 404 are both "done" for the caller (SCR-031). */
export async function deleteTrip(tripId: Uuid): Promise<void> {
  try {
    await apiRequest<void>(`/v1/trips/${encodeURIComponent(tripId)}`, { method: 'DELETE' });
  } catch (error) {
    if (!(error instanceof ApiError && error.status === 404)) throw error;
  }
}

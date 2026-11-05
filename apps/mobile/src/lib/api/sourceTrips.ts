/**
 * Save, booking handoff and trip deletion calls (SCR-029, SCR-037, SCR-031). Same rules as `source.ts`: remote when
 * `isRemoteEnabled()` (EXPO_PUBLIC_API_URL set, see config.ts), otherwise served from local fixtures. Types missing from `types.ts` are mirrored here from docs/04-design/api/openapi.yaml.
 */
import { currentLocale } from '../../i18n';
import { apiRequest, apiRequestRaw } from './client';
import { isRemoteEnabled } from './config';
import { ApiError } from './errors';
import { cityById, fixtureTripDetail, fixtureTrips } from './fixtures/da-nang';
import type { Conflict, HandoffKind, HandoffLink, IsoDate, IsoDateTime, Money, TripDetail, Uuid } from './types';

/* ---------------------------------------------------------------- Contract mirrors */

/** `AcceptPreviewRequest` (API-022 body). Both revisions are always sent (ADR-009). */
export type AcceptPreviewRequest = {
  expected_preview_revision: number;
  expected_trip_revision: number;
};

/** API-022 200 body plus the `Idempotent-Replayed` header (true when the server returned the original response). */
export type AcceptPreviewResult = {
  trip: TripDetail;
  replayed: boolean;
};

/** `StayPrice` (API-031 item). Runtime only; never cached or stored (FR-081). */
export type StayPrice = {
  name: string;
  price: Money;
  price_basis?: 'PER_NIGHT' | 'TOTAL_STAY';
  provider_key: string;
  handoff_url?: string | null;
  retrieved_at: IsoDateTime;
};

/** `StayPricePage` (API-031). */
export type StayPricePage = {
  items: StayPrice[];
  next_cursor: string | null;
  /** Partner confirms the final price (FR-080). */
  notice: string;
  attribution_text: string;
  retrieved_at: IsoDateTime;
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

/* ---------------------------------------------------------------- Fixture plumbing */

const wait = (ms: number) => new Promise<void>(resolve => setTimeout(resolve, ms));

/**
 * Dev switch for the Save outcome (fixtures only). Set it from a dev menu with `setAcceptScenario`, or start the app with
 * `EXPO_PUBLIC_FIXTURE_SAVE_OUTCOME=success|plan_blocked|revision_conflict|interrupted|expired`.
 * - `success`: 200, the trip revision moves to `expected_trip_revision + 1`.
 * - `plan_blocked`: 409 with `context.reasons`.
 * - `revision_conflict`: the trip was saved elsewhere first; 409 until the request carries the newer revision.
 * - `interrupted`: the first request with a key completes server-side but the response is lost; a retry with the same
 *   key replays the original 200 (`Idempotent-Replayed: true`).
 * - `expired`: 410 `preview_expired`.
 */
export type AcceptScenario = 'success' | 'plan_blocked' | 'revision_conflict' | 'interrupted' | 'expired';

const scenarios: AcceptScenario[] = ['success', 'plan_blocked', 'revision_conflict', 'interrupted', 'expired'];
const envScenario = process.env.EXPO_PUBLIC_FIXTURE_SAVE_OUTCOME as AcceptScenario | undefined;
let acceptScenario: AcceptScenario = envScenario && scenarios.includes(envScenario) ? envScenario : 'success';

export function setAcceptScenario(next: AcceptScenario) {
  acceptScenario = next;
  otherDeviceSaved.clear();
}

export function getAcceptScenario(): AcceptScenario {
  return acceptScenario;
}

/** Idempotency store: key → the body it was first used with and the stored 200 response. */
const idempotency = new Map<string, { body: string; trip: TripDetail }>();
/** Fixture-server trip revisions after saves. */
const serverRevision = new Map<Uuid, number>();
/** Trips that another device has already saved in the conflict scenario. */
const otherDeviceSaved = new Set<Uuid>();

const previewTripId = (_previewId: Uuid): Uuid => fixtureTrips[0].id;

/* ---------------------------------------------------------------- Calls */

/**
 * API-022 `POST /v1/plan-previews/{preview_id}/accept` with a required `Idempotency-Key`. Replaying the same key and
 * body returns the original trip with `replayed: true`; the same key with a different body is 409
 * `idempotency_key_reused`. Errors: 409 `plan_blocked` (`context.reasons`), 409 `revision_conflict`
 * (`context.current_revision`), 410 `preview_expired`, `NetworkError` when no response arrived.
 */
export async function acceptPreview(previewId: Uuid, body: AcceptPreviewRequest, idempotencyKey: string): Promise<AcceptPreviewResult> {
  if (isRemoteEnabled()) {
    try {
      const response = await apiRequestRaw<TripDetail>(`/v1/plan-previews/${encodeURIComponent(previewId)}/accept`, { body, idempotencyKey, method: 'POST' });
      return { replayed: response.headers.get('Idempotent-Replayed') === 'true', trip: response.data };
    } catch (error) {
      // No response: the save may have committed; the caller retries with the same key.
      if (error instanceof TypeError) throw new NetworkError();
      throw error;
    }
  }
  await wait(900);
  const serialized = JSON.stringify(body);
  const stored = idempotency.get(idempotencyKey);
  if (stored) {
    if (stored.body !== serialized) {
      throw new ApiError({ code: 'idempotency_key_reused', message: 'Invalid request. Try again.', retryable: false }, 409);
    }
    return { replayed: true, trip: stored.trip };
  }

  const tripId = previewTripId(previewId);
  const base = fixtureTripDetail(tripId, currentLocale());
  if (!base) throw new ApiError({ code: 'not_found', message: 'This item was not found', retryable: false }, 404);
  const current = serverRevision.get(tripId) ?? base.revision;

  if (acceptScenario === 'expired') {
    throw new ApiError({ code: 'preview_expired', message: 'This draft expired', retryable: false }, 410);
  }
  if (acceptScenario === 'plan_blocked') {
    const reasons: Conflict[] = [{ message: currentLocale() === 'vi' ? 'Không có tuyến đường giữa hai điểm dừng' : 'No route between two stops', severity: 'BLOCKING', type: 'LEG_UNAVAILABLE' }];
    throw new ApiError({ code: 'plan_blocked', context: { reasons }, message: 'This trip cannot be saved yet', retryable: false }, 409);
  }
  if (acceptScenario === 'revision_conflict' && !otherDeviceSaved.has(tripId)) {
    otherDeviceSaved.add(tripId);
    serverRevision.set(tripId, current + 1);
  }
  const latest = serverRevision.get(tripId) ?? current;
  if (body.expected_trip_revision !== latest) {
    throw new ApiError({ code: 'revision_conflict', context: { current_revision: latest }, message: 'This draft changed elsewhere', retryable: false }, 409);
  }

  const now = new Date().toISOString();
  const trip: TripDetail = { ...base, active_preview_id: null, revision: latest + 1, saved_at: now, status: 'SAVED', updated_at: now };
  serverRevision.set(tripId, trip.revision);
  idempotency.set(idempotencyKey, { body: serialized, trip });
  if (acceptScenario === 'interrupted') {
    // The save committed, but the response never reaches the device; the retry replays it.
    throw new NetworkError();
  }
  return { replayed: false, trip };
}

const isoAddDays = (date: IsoDate, days: number): IsoDate => {
  const [y, m, d] = date.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d + days)).toISOString().slice(0, 10);
};

/**
 * API-030 `GET /v1/trips/{trip_id}/handoff-links?kind[&stop_id]`, one request per kind. The contract 200 body is a single
 * `HandoffLink`; SCR-037 lists `items[]` (two STAY partners), so the fixture returns every partner for the requested
 * kinds. Requires a SAVED trip (409 `trip_not_saved`). `end_date` = check-out = start + day_count.
 */
export async function getHandoffLinks(tripId: Uuid, options: { kinds?: HandoffKind[]; stopId?: Uuid } = {}): Promise<HandoffLink[]> {
  if (isRemoteEnabled()) {
    const kinds = options.kinds ?? ['STAY', 'ACTIVITY', 'TRANSPORT'];
    return Promise.all(kinds.map(kind => apiRequest<HandoffLink>(`/v1/trips/${encodeURIComponent(tripId)}/handoff-links`, {
      query: { kind, locale: currentLocale(), stop_id: options.stopId },
    })));
  }
  await wait(450);
  const trip = fixtureTrips.find(item => item.id === tripId);
  if (!trip) throw new ApiError({ code: 'not_found', message: 'This item was not found', retryable: false }, 404);
  if (trip.status !== 'SAVED') throw new ApiError({ code: 'trip_not_saved', message: 'Save the trip first', retryable: false }, 409);
  const kinds = options.kinds ?? ['STAY', 'ACTIVITY', 'TRANSPORT'];
  const city = cityById(trip.city_id);
  const name = city?.name_en ?? '';
  const q = encodeURIComponent(name);
  const start = trip.start_date;
  const end = isoAddDays(start, trip.day_count);
  const base = { city_id: trip.city_id, end_date: end, start_date: start };
  const links: HandoffLink[] = [];
  if (kinds.includes('STAY')) {
    links.push(
      { ...base, kind: 'STAY', partner_display_name: 'Agoda', partner_key: 'agoda', url: `https://www.agoda.com/search?textToSearch=${q}&checkIn=${start}&checkOut=${end}&rooms=1&adults=2` },
      { ...base, kind: 'STAY', partner_display_name: 'Booking.com', partner_key: 'booking_com', url: `https://www.booking.com/searchresults.html?ss=${q}&checkin=${start}&checkout=${end}&group_adults=2&no_rooms=1` },
    );
  }
  if (kinds.includes('ACTIVITY')) {
    links.push({ ...base, kind: 'ACTIVITY', partner_display_name: 'Klook', partner_key: 'klook', url: `https://www.klook.com/search/result/?query=${q}` });
  }
  if (kinds.includes('TRANSPORT')) {
    const slug = city?.code ?? '';
    const origin = slug === 'ha-noi' ? 'ho-chi-minh-city' : 'ha-noi';
    links.push({ ...base, kind: 'TRANSPORT', partner_display_name: '12Go', partner_key: 'twelve_go', url: `https://12go.asia/en/travel/${origin}/${slug}?date=${start}` });
  }
  return links;
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
  if (isRemoteEnabled()) return apiRequest<StayPricePage>(`/v1/trips/${encodeURIComponent(tripId)}/stay-prices`);
  await wait(700);
  if (!fixtureTrips.some(item => item.id === tripId)) {
    throw new ApiError({ code: 'not_found', message: 'This item was not found', retryable: false }, 404);
  }
  const retrieved_at = new Date().toISOString();
  const offer = (name: string, amount: string, handoff_url: string): StayPrice => ({
    handoff_url, name, price: { amount, currency: 'VND' }, price_basis: 'PER_NIGHT', provider_key: 'liteapi', retrieved_at,
  });
  return {
    attribution_text: 'Giá do LiteAPI cung cấp · Prices by LiteAPI',
    items: [
      offer('Little Riverside Hoi An', '1850000', 'https://www.agoda.com/search?textToSearch=Little%20Riverside%20Hoi%20An'),
      offer('Hoi An Garden Homestay', '620000', 'https://www.booking.com/searchresults.html?ss=Hoi%20An%20Garden%20Homestay'),
      offer('Old Town Boutique Villa', '980000', 'https://www.booking.com/searchresults.html?ss=Old%20Town%20Boutique%20Villa'),
    ],
    next_cursor: null,
    notice: 'The partner confirms the final price.',
    retrieved_at,
  };
}

/** API-016 `DELETE /v1/trips/{trip_id}`. 204 and 404 are both "done" for the caller (SCR-031). */
export async function deleteTrip(tripId: Uuid): Promise<void> {
  if (isRemoteEnabled()) {
    try {
      await apiRequest<void>(`/v1/trips/${encodeURIComponent(tripId)}`, { method: 'DELETE' });
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 404)) throw error;
    }
    return;
  }
  await wait(400);
  serverRevision.delete(tripId);
  otherDeviceSaved.delete(tripId);
}

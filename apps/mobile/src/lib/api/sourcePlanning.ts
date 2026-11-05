/**
 * Proposal editing data source: API-019 head read, API-020 `editPlanPreview`, API-021 `regeneratePlanDay`, and the
 * SCR-028 picker search (API-010 with `category_code`). With EXPO_PUBLIC_USE_FIXTURES=1 everything is served by the
 * FIXTURE below; otherwise calls throw until the API client lands (TASK-001).
 *
 * The client never computes times, distances, durations or Plan Health: it sends an op list (`edits[]`) and renders
 * whatever revision comes back.
 */
import * as Crypto from 'expo-crypto';
import { currentLocale } from '../../i18n';
import { defaultCity, fixturePlaces } from './fixtures/hoi-an';
import { ApiError, getPreview, searchPlaces, useFixtures } from './source';
import type {
  Conflict,
  Day,
  ErrorDetail,
  Leg,
  Locale,
  Place,
  PlanHealth,
  PlanPreview,
  PlanningStage,
  PlanningStreamEvent,
  Stop,
  TravelMode,
  Uuid,
} from './types';

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
  return Crypto.randomUUID();
}

function notWired(): never {
  throw new Error('API not wired yet (TASK-001)');
}

function wait(ms: number, signal?: AbortSignal): Promise<boolean> {
  return new Promise(resolve => {
    if (signal?.aborted) { resolve(false); return; }
    const timer = setTimeout(() => { signal?.removeEventListener('abort', onAbort); resolve(true); }, ms);
    function onAbort() { clearTimeout(timer); resolve(false); }
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

/* ---------------------------------------------------------------- Public calls */

/** API-019 `GET /v1/plan-previews/{preview_id}`: the head revision (fixture: the edited head if one exists). */
export async function getPreviewHead(previewId: Uuid): Promise<PlanPreview> {
  if (!useFixtures) notWired();
  const head = fixtureHeads.get(previewId);
  if (head) { await wait(250); return clone(head); }
  const preview = await getPreview(previewId);
  seed(preview);
  return clone(preview);
}

/**
 * API-020 `PATCH /v1/plan-previews/{preview_id}` with `Idempotency-Key`. Resolves with the new head revision; rejects
 * with `ApiError` (409 `revision_conflict`, 410, 422, 503 `route_unavailable`) or a network `TypeError`.
 */
export async function editPreview(previewId: Uuid, body: PlanPreviewEdit, idempotencyKey: string): Promise<PlanPreview> {
  if (!useFixtures) notWired();
  await wait(600);
  return fixtureEdit(previewId, body, idempotencyKey);
}

const regenerationStages: PlanningStage[] = ['VALIDATING_REQUEST', 'SELECTING_PLACES', 'ROUTING', 'SCHEDULING', 'CHECKING_HEALTH'];

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
  if (!useFixtures) notWired();
  for (const stage of regenerationStages) {
    if (!(await wait(600, signal))) return;
    onEvent({ stage, type: 'progress' });
  }
  if (!(await wait(400, signal))) return;
  try {
    const next = fixtureRegenerate(previewId, body, idempotencyKey);
    onEvent({ plan_health: next.plan_health, preview_id: next.id, preview_revision: next.preview_revision, type: 'preview_ready' });
  } catch (error) {
    onEvent({ error: error instanceof ApiError ? error.error : { code: 'internal_error', message: 'Something went wrong', retryable: true }, type: 'error' });
  }
}

/** API-010 `GET /v1/places?city_id&q&category_code` (published places of the trip's city only). */
export async function searchCityPlaces(cityId: Uuid, q?: string, categoryCode?: string | null): Promise<Place[]> {
  if (!useFixtures) notWired();
  const query = q?.trim() || undefined;
  const base = await searchPlaces(cityId, query);
  const all = [...base, ...extraPlaces(currentLocale(), query).filter(place => place.city_id === cityId)];
  const items = categoryCode ? all.filter(place => place.category_code === categoryCode) : all;
  items.forEach(place => placeCache.set(place.id, place));
  return items;
}

/** A place seen in a recent picker search (display only: photo, category). */
export function cachedPlace(placeId: Uuid): Place | undefined {
  return placeCache.get(placeId);
}

const placeCache = new Map<Uuid, Place>();

/* ================================================================ FIXTURE ONLY ================================== */
/*
 * Everything below simulates the server for UI work. It is NOT scheduling logic and must never be ported:
 * - Times come from a fixed per-day SLOT TABLE: the stop at position k of a day always shows slot k, whatever its
 *   duration. Visit durations never move times here; the real server re-schedules with OR-Tools (ADR-011).
 * - Legs are reused from the previous revision when the same pair and mode survive; otherwise the leg at position k
 *   copies a fixed LEG TABLE entry for its mode. Nothing is measured; the real server calls Google Routes.
 * - "Plan Health" is the summary of the conflicts the fixture stops/legs already carry (server-shaped output only).
 */

type FixtureFault = 'network' | 'route_unavailable' | 'revision_conflict' | 'ai_unavailable' | 'preview_expired';

const FAULTS: FixtureFault[] = ['network', 'route_unavailable', 'revision_conflict', 'ai_unavailable', 'preview_expired'];
const envFault = process.env.EXPO_PUBLIC_FIXTURE_EDIT_FAULT as FixtureFault | undefined;
let nextFault: FixtureFault | null = envFault && FAULTS.includes(envFault) ? envFault : null;

/** FIXTURE: the next edit or regeneration fails once with `fault` (then calls succeed again). */
export function setFixtureNextFault(fault: FixtureFault | null) {
  nextFault = fault;
}
export function fixtureNextFault(): FixtureFault | null {
  return nextFault;
}
export const fixtureFaults = FAULTS;
export type { FixtureFault };

function takeFault(): FixtureFault | null {
  const fault = nextFault;
  nextFault = null;
  return fault;
}

const fixtureHeads = new Map<Uuid, PlanPreview>();
const idempotentReplies = new Map<string, PlanPreview>();
let stopSeq = 0;

const fid = (n: number) => `00000000-0000-4000-8000-${n.toString(16).padStart(12, '0')}`;
const byLocale = (locale: Locale, vi: string, en: string) => (locale === 'vi' ? vi : en);
const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

function apiError(status: number, code: string, message: string, retryable = false, context?: Record<string, unknown>): ApiError {
  const error: ErrorDetail = { code, message, retryable, ...(context ? { context } : {}) };
  return new ApiError(error, status);
}

function seed(preview: PlanPreview) {
  if (!fixtureHeads.has(preview.id)) fixtureHeads.set(preview.id, clone(preview));
}

async function headOrSeed(previewId: Uuid): Promise<PlanPreview> {
  const head = fixtureHeads.get(previewId);
  if (head) return head;
  const preview = await getPreview(previewId).catch(() => { throw apiError(404, 'not_found', 'This item was not found'); });
  seed(preview);
  return fixtureHeads.get(previewId) as PlanPreview;
}

/** FIXTURE slot table (HH:MM pairs). Position k of day d shows `SLOTS[d][k]`; positions past the table show no time. */
const SLOTS: Record<number, [string, string][]> = {
  1: [['08:00', '08:40'], ['08:45', '09:25'], ['09:30', '10:15'], ['10:20', '11:30'], ['17:30', '19:00'], ['19:15', '20:00'], ['13:30', '14:30'], ['15:00', '16:00']],
  2: [['08:30', '10:00'], ['10:20', '12:30'], ['14:00', '15:00'], ['15:20', '16:20'], ['16:40', '17:40']],
  3: [['08:30', '09:30'], ['09:45', '10:45'], ['11:00', '12:00'], ['14:00', '15:00'], ['15:20', '16:20']],
};
const DAY_DATES: Record<number, string> = { 1: '2027-01-16', 2: '2027-01-17', 3: '2027-01-18' };

/** FIXTURE leg table: [distance_m, duration_s] for the leg at position k of day d, per mode. Not measured. */
const LEGS: Record<number, Record<TravelMode, [number, number]>[]> = {
  1: [
    { DRIVE: [700, 240], WALK: [250, 240] }, { DRIVE: [800, 240], WALK: [300, 270] }, { DRIVE: [600, 180], WALK: [200, 180] },
    { DRIVE: [1500, 360], WALK: [650, 540] }, { DRIVE: [1200, 300], WALK: [450, 360] }, { DRIVE: [1100, 300], WALK: [400, 330] },
  ],
  2: [{ DRIVE: [6800, 960], WALK: [6800, 5100] }, { DRIVE: [4600, 720], WALK: [3900, 2880] }, { DRIVE: [3200, 540], WALK: [1800, 1380] }],
  3: [{ DRIVE: [2100, 420], WALK: [900, 690] }, { DRIVE: [2600, 480], WALK: [1100, 840] }, { DRIVE: [1900, 360], WALK: [700, 540] }],
};

const at = (day: number, time: string) => `${DAY_DATES[day] ?? DAY_DATES[1]}T${time}:00+07:00`;

/** FIXTURE: places that are not in hoi-an.ts but make the picker useful (no photos; approximate coordinates). */
type Extra = { pid: number; slug: string; category_code: string; name_vi: string; name_en: string; short_vi: string; short_en: string; lat: number; lng: number; visit: number };
const EXTRAS: Extra[] = [
  { category_code: 'heritage', lat: 15.87712, lng: 108.32905, name_en: 'Hoi An Museum of History and Culture', name_vi: 'Bảo tàng Lịch sử Văn hoá Hội An', pid: 0x4a1, short_en: 'Small museum on the town’s trading history.', short_vi: 'Bảo tàng nhỏ về lịch sử thương cảng Hội An.', slug: 'bao-tang-lich-su-van-hoa', visit: 45 },
  { category_code: 'heritage', lat: 15.87701, lng: 108.32742, name_en: 'Cantonese Assembly Hall', name_vi: 'Hội quán Quảng Đông', pid: 0x4a2, short_en: 'Assembly hall with a dragon fountain courtyard.', short_vi: 'Hội quán có sân rồng phun nước.', slug: 'hoi-quan-quang-dong', visit: 30 },
  { category_code: 'heritage', lat: 15.87705, lng: 108.32655, name_en: 'Phung Hung Ancient House', name_vi: 'Nhà cổ Phùng Hưng', pid: 0x4a3, short_en: 'Two-storey merchant house near the bridge.', short_vi: 'Nhà buôn hai tầng gần Chùa Cầu.', slug: 'nha-co-phung-hung', visit: 30 },
  { category_code: 'nature', lat: 15.88290, lng: 108.30860, name_en: 'Thanh Ha Pottery Village', name_vi: 'Làng gốm Thanh Hà', pid: 0x4a4, short_en: 'Riverside pottery village west of the old town.', short_vi: 'Làng gốm ven sông phía tây phố cổ.', slug: 'lang-gom-thanh-ha', visit: 75 },
  { category_code: 'market', lat: 15.87655, lng: 108.32560, name_en: 'Hoi An Night Market', name_vi: 'Chợ đêm Hội An', pid: 0x4a5, short_en: 'Lantern-lit stalls on Nguyen Hoang street.', short_vi: 'Dãy hàng đèn lồng trên đường Nguyễn Hoàng.', slug: 'cho-dem-hoi-an', visit: 60 },
  { category_code: 'beach', lat: 15.89520, lng: 108.36310, name_en: 'Cua Dai Beach', name_vi: 'Biển Cửa Đại', pid: 0x4a6, short_en: 'Long sandy beach east of the old town.', short_vi: 'Bãi cát dài phía đông phố cổ.', slug: 'bien-cua-dai', visit: 120 },
];

function fold(value: string) {
  return value.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase();
}

function extraPlaces(locale: Locale, q?: string): Place[] {
  const query = q ? fold(q) : '';
  return EXTRAS
    .filter(place => !query || fold(place.name_vi).includes(query) || fold(place.name_en).includes(query))
    .map(place => ({
      catalog_publication_id: fid(0x301),
      category_code: place.category_code,
      city_id: defaultCity.id,
      id: fid(place.pid),
      location: { latitude: place.lat, longitude: place.lng },
      name: byLocale(locale, place.name_vi, place.name_en),
      name_vi: place.name_vi,
      short_description: byLocale(locale, place.short_vi, place.short_en),
      slug: place.slug,
      thumbnail: null,
      visit_minutes_suggested: place.visit,
    }));
}

function cityPool(locale: Locale): Place[] {
  return [...fixturePlaces(locale), ...extraPlaces(locale)];
}

function stopForPlace(place: Place, visitMinutes?: number): Stop {
  stopSeq += 1;
  placeCache.set(place.id, place);
  return {
    catalog_publication_id: place.catalog_publication_id,
    conflicts: [],
    id: fid(0xc000 + stopSeq),
    is_locked: false,
    location: place.location,
    name: place.name,
    name_vi: place.name_vi,
    ordinal: 0,
    place_id: place.id,
    rationale: null,
    visit_minutes: visitMinutes ?? place.visit_minutes_suggested ?? 60,
  };
}

/** FIXTURE re-layout: slot times by position, legs reused or copied from the leg table. Not scheduling. */
function relayout(days: Day[], previous: Day[], modeOverrides: Map<string, TravelMode>): Day[] {
  const pair = (from: Uuid, to: Uuid) => `${from}>${to}`;
  const previousLegs = new Map(previous.flatMap(day => day.legs).map(leg => [pair(leg.from_stop_id, leg.to_stop_id), leg]));
  return days.map(day => {
    const slots = SLOTS[day.day_index] ?? SLOTS[1];
    const stops = day.stops.map((stop, index) => {
      const slot = slots[index];
      return { ...stop, ordinal: index + 1, planned_arrival: slot ? at(day.day_index, slot[0]) : null, planned_departure: slot ? at(day.day_index, slot[1]) : null };
    });
    const legs: Leg[] = [];
    for (let index = 0; index < stops.length - 1; index += 1) {
      const from = stops[index];
      const to = stops[index + 1];
      const key = pair(from.id, to.id);
      const override = modeOverrides.get(key);
      const kept = previousLegs.get(key);
      if (kept && (!override || override === kept.travel_mode)) { legs.push(kept); continue; }
      const mode: TravelMode = override ?? kept?.travel_mode ?? (day.day_index === 2 ? 'DRIVE' : 'WALK');
      const table = LEGS[day.day_index] ?? LEGS[1];
      const [distance_m, duration_s] = table[index % table.length][mode];
      legs.push({ availability: 'AVAILABLE', conflicts: [], distance_m, duration_s, from_stop_id: from.id, measured_at: new Date().toISOString(), to_stop_id: to.id, travel_mode: mode });
    }
    return { ...day, legs, stops };
  });
}

/** FIXTURE: Plan Health as the summary of conflicts already attached to the fixture stops and legs. */
function summarise(days: Day[]): { plan_health: PlanHealth; health_reasons: Conflict[] } {
  const all = days.flatMap(day => [...day.stops.flatMap(stop => stop.conflicts ?? []), ...day.legs.flatMap(leg => leg.conflicts ?? [])]);
  const reasons: Conflict[] = [];
  for (const conflict of all) {
    if (!reasons.some(reason => reason.type === conflict.type && reason.severity === conflict.severity)) reasons.push(conflict);
  }
  const plan_health: PlanHealth = all.some(item => item.severity === 'BLOCKING') ? 'BLOCKED' : all.length ? 'WARNING' : 'GOOD';
  return { health_reasons: reasons, plan_health };
}

function commit(head: PlanPreview, days: Day[], origin: PlanPreview['origin'], modeOverrides = new Map<string, TravelMode>()): PlanPreview {
  const laidOut = relayout(days, head.days, modeOverrides);
  const revision = head.head_revision + 1;
  const next: PlanPreview = {
    ...head,
    ...summarise(laidOut),
    created_at: new Date().toISOString(),
    days: laidOut,
    head_revision: revision,
    origin,
    parent_revision: head.preview_revision,
    preview_revision: revision,
  };
  fixtureHeads.set(head.id, next);
  return next;
}

function faultError(fault: FixtureFault): Error {
  switch (fault) {
    case 'network': return new TypeError('Network request failed');
    case 'route_unavailable': return apiError(503, 'route_unavailable', 'Could not recalculate travel times', true);
    case 'ai_unavailable': return apiError(503, 'ai_unavailable', 'The AI service is busy', true);
    case 'preview_expired': return apiError(410, 'preview_expired', 'This draft expired');
    case 'revision_conflict': return apiError(409, 'revision_conflict', 'This draft changed elsewhere', false);
  }
}

/** FIXTURE 409: another device appended a revision (same itinerary, new revision number). */
function simulateOtherDevice(head: PlanPreview) {
  const revision = head.head_revision + 1;
  fixtureHeads.set(head.id, { ...head, head_revision: revision, parent_revision: head.preview_revision, preview_revision: revision });
}

async function fixtureEdit(previewId: Uuid, body: PlanPreviewEdit, idempotencyKey: string): Promise<PlanPreview> {
  const replay = idempotentReplies.get(idempotencyKey);
  if (replay) return clone(replay);
  const head = await headOrSeed(previewId);
  const fault = takeFault();
  if (fault === 'revision_conflict') { simulateOtherDevice(head); throw faultError(fault); }
  if (fault) throw faultError(fault);
  if (head.status !== 'ACTIVE') throw apiError(410, 'preview_closed', 'This draft is closed');
  if (body.expected_revision !== head.head_revision) throw apiError(409, 'revision_conflict', 'This draft changed elsewhere');
  if (!body.edits.length || body.edits.length > MAX_EDITS_PER_REQUEST) throw apiError(422, 'validation_failed', 'Check the highlighted fields', false, { fields: ['edits'] });

  const locale = currentLocale();
  const pool = cityPool(locale);
  const days: Day[] = clone(head.days);
  const modeOverrides = new Map<string, TravelMode>();
  const invalid = (field: string) => apiError(422, 'validation_failed', 'Check the highlighted fields', false, { fields: [field] });
  const find = (stopId: Uuid) => {
    for (const day of days) {
      const index = day.stops.findIndex(stop => stop.id === stopId);
      if (index >= 0) return { day, index, stop: day.stops[index] };
    }
    throw invalid('stop_id');
  };
  const dayOf = (dayIndex: number) => days.find(day => day.day_index === dayIndex) ?? (() => { throw invalid('day_index'); })();
  const placeOf = (placeId: Uuid) => {
    const place = pool.find(item => item.id === placeId);
    if (!place) throw apiError(422, 'place_not_in_city', 'This place is not in the trip’s city');
    if (days.some(day => day.stops.some(stop => stop.place_id === placeId))) throw invalid('place_id');
    return place;
  };
  const insertAt = (list: Stop[], stop: Stop, ordinal?: number) => {
    const index = ordinal ? Math.min(Math.max(ordinal - 1, 0), list.length) : list.length;
    list.splice(index, 0, stop);
  };

  for (const edit of body.edits) {
    switch (edit.op) {
      case 'MOVE_STOP': {
        const { day, index, stop } = find(edit.stop_id);
        const target = dayOf(edit.day_index);
        if (stop.is_locked && target.day_index !== day.day_index) throw invalid('stop_id');
        day.stops.splice(index, 1);
        if (target.stops.length >= MAX_STOPS_PER_DAY) throw invalid('day_index');
        insertAt(target.stops, stop, edit.to_ordinal);
        break;
      }
      case 'ADD_STOP': {
        const target = dayOf(edit.day_index);
        if (target.stops.length >= MAX_STOPS_PER_DAY) throw invalid('day_index');
        insertAt(target.stops, stopForPlace(placeOf(edit.place_id)), edit.to_ordinal);
        break;
      }
      case 'REMOVE_STOP': {
        const { day, index, stop } = find(edit.stop_id);
        if (stop.is_locked) throw invalid('stop_id');
        day.stops.splice(index, 1);
        break;
      }
      case 'REPLACE_STOP': {
        const { day, index } = find(edit.stop_id);
        day.stops.splice(index, 1, stopForPlace(placeOf(edit.place_id)));
        break;
      }
      case 'SET_VISIT_MINUTES': {
        if (edit.visit_minutes < 5 || edit.visit_minutes > 600) throw invalid('visit_minutes');
        find(edit.stop_id).stop.visit_minutes = edit.visit_minutes;
        break;
      }
      case 'SET_LEG_MODE': {
        find(edit.from_stop_id);
        find(edit.to_stop_id);
        modeOverrides.set(`${edit.from_stop_id}>${edit.to_stop_id}`, edit.travel_mode);
        break;
      }
      case 'LOCK_STOP':
      case 'UNLOCK_STOP':
        find(edit.stop_id).stop.is_locked = edit.op === 'LOCK_STOP';
        break;
    }
  }

  const next = commit(head, days, 'MANUAL_EDIT', modeOverrides);
  idempotentReplies.set(idempotencyKey, next);
  return clone(next);
}

function fixtureRegenerate(previewId: Uuid, body: RegenerateDayRequest, idempotencyKey: string): PlanPreview {
  const replay = idempotentReplies.get(idempotencyKey);
  if (replay) return clone(replay);
  const head = fixtureHeads.get(previewId);
  if (!head) throw apiError(404, 'not_found', 'This item was not found');
  const fault = takeFault();
  if (fault === 'revision_conflict') { simulateOtherDevice(head); throw faultError(fault); }
  if (fault) throw faultError(fault);
  if (body.expected_revision !== head.head_revision) throw apiError(409, 'revision_conflict', 'This draft changed elsewhere');

  const locale = body.locale ?? currentLocale();
  const days: Day[] = clone(head.days);
  const day = days.find(item => item.day_index === body.day_index);
  if (!day) throw apiError(422, 'validation_failed', 'Check the highlighted fields', false, { fields: ['day_index'] });
  const locked = new Set([...(body.locked_stop_ids ?? []), ...day.stops.filter(stop => stop.is_locked).map(stop => stop.id)]);
  const taken = new Set(days.flatMap(item => item.stops.filter(stop => item !== day || locked.has(stop.id)).map(stop => stop.place_id)));
  // FIXTURE "selection": rotate through the city pool by revision so each regeneration shows a different set.
  const pool = cityPool(locale).filter(place => !taken.has(place.id) && !day.stops.some(stop => stop.place_id === place.id && !locked.has(stop.id)));
  const rotated = [...pool.slice(head.head_revision % Math.max(pool.length, 1)), ...pool.slice(0, head.head_revision % Math.max(pool.length, 1))];
  const fresh = rotated.length ? rotated : cityPool(locale).filter(place => !taken.has(place.id));
  let cursor = 0;
  const target = Math.max(day.stops.length, 3);
  const stops: Stop[] = [];
  for (let index = 0; index < target; index += 1) {
    const existing = day.stops[index];
    if (existing && locked.has(existing.id)) { stops.push({ ...existing, is_locked: true }); continue; }
    const place = fresh[cursor++];
    if (!place) continue;
    stops.push({ ...stopForPlace(place), rationale: byLocale(locale, 'Gợi ý mới cho ngày này (dữ liệu mẫu).', 'A fresh pick for this day (sample data).') });
  }
  day.stops = stops;
  const next = commit(head, days, 'DAY_REGENERATED');
  idempotentReplies.set(idempotencyKey, next);
  return clone(next);
}

import { useCallback, useEffect, useRef, useState } from 'react';
import { currentLocale } from '../../../i18n';
import { ApiError, getPlace, getTrip, listCities } from '../../../lib/api/source';
import { cachedPlace, getPreviewHead } from '../../../lib/api/sourcePlanning';
import type { CityCode, Conflict, IsoDate, Media, PlanHealth, PlanPreview, TravelMode, TripDetail, Uuid } from '../../../lib/api/types';
import { numberDays, type NumberedDay } from './model';

/** What SCR-024/025 render: a preview (editable draft) or a saved itinerary (read-only), in one shape. */
export type ProposalData = {
  days: NumberedDay[];
  /** Server Plan Health; null for a saved itinerary (API-014 carries none). */
  health: PlanHealth | null;
  healthReasons: Conflict[];
  readOnly: boolean;
  saved: boolean;
  startDate: IsoDate | null;
  cityName: string | null;
  /** City code, for the city cover photo when the first stop has no photo. */
  cityCode: CityCode | null;
  cover: Media | null;
  /** Display-only place data per `place_id` (photo, category icon); never planner input. */
  places: Record<Uuid, StopPlace>;
  /** Preview identity for edits (API-020 `expected_revision`); null for a saved itinerary. */
  previewId: Uuid | null;
  previewRevision: number | null;
  origin: PlanPreview['origin'] | null;
  tripId: Uuid | null;
  cityId: Uuid | null;
  /** Modes the Edit stop sheet may offer (trip `planning_preferences.allowed_modes`). */
  allowedModes: TravelMode[];
};

export type StopPlace = { thumbnail: Media | null; categoryCode: string | null };

export type ProposalState =
  | { status: 'loading' }
  | { status: 'error'; code: string }
  | { status: 'ready'; data: ProposalData };

type Params = { previewId: Uuid; tripId?: Uuid; mode?: 'saved' | 'draft' };

async function cityOf(cityId: Uuid | undefined): Promise<{ cityName: string | null; cityCode: CityCode | null }> {
  const none = { cityCode: null, cityName: null };
  if (!cityId) return none;
  const cities = await listCities().catch(() => []);
  const city = cities.find(item => item.id === cityId);
  if (!city) return none;
  return { cityCode: city.code, cityName: currentLocale() === 'vi' ? city.name_vi : city.name_en };
}

/** Photo and category of every stop's place (API-011), loaded in parallel; a failed lookup just shows no photo. */
async function placesOf(days: NumberedDay[], known: Record<Uuid, StopPlace> = {}): Promise<Record<Uuid, StopPlace>> {
  // WEB_UNVERIFIED stops have no catalog place (place_id null): nothing to look up.
  const ids = [...new Set(days.flatMap(day => day.stops.map(stop => stop.place_id)).filter((id): id is Uuid => !!id))];
  const entries = await Promise.all(ids.map(id => {
    if (known[id]) return [id, known[id]] as const;
    const seen = cachedPlace(id);
    if (seen) return [id, { categoryCode: seen.category_code, thumbnail: seen.thumbnail }] as const;
    return getPlace(id)
      .then(place => [id, { categoryCode: place.category_code, thumbnail: place.thumbnail }] as const)
      .catch(() => [id, { categoryCode: null, thumbnail: null }] as const);
  }));
  return Object.fromEntries(entries);
}

function coverOf(days: NumberedDay[], places: Record<Uuid, StopPlace>): Media | null {
  const first = days.find(day => day.stops.length)?.stops[0];
  return first?.place_id ? places[first.place_id]?.thumbnail ?? null : null;
}

async function fromTrip(trip: TripDetail): Promise<ProposalData> {
  const days = numberDays(trip.days);
  const [city, places] = await Promise.all([cityOf(trip.city_id), placesOf(days)]);
  return {
    ...city, allowedModes: modesOf(trip), cityId: trip.city_id, cover: coverOf(days, places), days, health: null, healthReasons: [],
    origin: null, places, previewId: null, previewRevision: null, readOnly: trip.status === 'SAVED', saved: trip.status === 'SAVED',
    startDate: trip.start_date, tripId: trip.id,
  };
}

const ALL_MODES: TravelMode[] = ['WALK', 'DRIVE'];

function modesOf(trip: TripDetail | null): TravelMode[] {
  const modes = trip?.planning_preferences?.allowed_modes;
  return modes?.length ? modes : ALL_MODES;
}

/**
 * Rebuilds the screen data for a new preview revision (after an edit or a regeneration). City, dates and cover stay;
 * days, health and revision come from the server body; only photos of new places are looked up.
 */
export async function withPreview(data: ProposalData, preview: PlanPreview): Promise<ProposalData> {
  const days = numberDays(preview.days);
  const places = await placesOf(days, data.places);
  return {
    ...data,
    days,
    health: preview.plan_health,
    healthReasons: preview.health_reasons ?? [],
    origin: preview.origin,
    places: { ...data.places, ...places },
    previewId: preview.id,
    previewRevision: preview.preview_revision,
    readOnly: preview.status !== 'ACTIVE',
    saved: preview.status === 'SAVED',
  };
}

async function load({ previewId, tripId, mode }: Params): Promise<ProposalData> {
  // Saved trip opened from My trips: the saved itinerary, read-only (SCR-024 saved read mode).
  if (mode === 'saved' && tripId) return fromTrip(await getTrip(tripId));

  let preview;
  try {
    preview = await getPreviewHead(previewId);
  } catch (error) {
    // No matching preview (e.g. previewId is the trip id): fall back to the trip's own itinerary.
    if (tripId && error instanceof ApiError && error.error.code === 'resource_not_found') return fromTrip(await getTrip(tripId));
    throw error;
  }
  const days = numberDays(preview.days);
  const [trip, places] = await Promise.all([getTrip(preview.trip_id).catch(() => null), placesOf(days)]);
  return {
    ...(await cityOf(trip?.city_id)),
    allowedModes: modesOf(trip),
    cityId: trip?.city_id ?? null,
    cover: coverOf(days, places),
    days,
    places,
    health: preview.plan_health,
    healthReasons: preview.health_reasons ?? [],
    origin: preview.origin,
    previewId: preview.id,
    previewRevision: preview.preview_revision,
    readOnly: preview.status !== 'ACTIVE',
    saved: preview.status === 'SAVED',
    startDate: trip?.start_date ?? null,
    tripId: preview.trip_id,
  };
}

export function useProposal(params: Params) {
  const [state, setState] = useState<ProposalState>({ status: 'loading' });
  const { previewId, tripId, mode } = params;

  const reload = useCallback(() => {
    let active = true;
    setState({ status: 'loading' });
    load({ mode, previewId, tripId })
      .then(data => { if (active) setState({ data, status: 'ready' }); })
      .catch((error: unknown) => {
        if (active) setState({ code: error instanceof ApiError ? error.error.code : 'internal_error', status: 'error' });
      });
    return () => { active = false; };
  }, [previewId, tripId, mode]);

  useEffect(() => reload(), [reload]);

  const latest = useRef(state);
  latest.current = state;

  /** Shows a newer preview revision in place (no skeleton); a stale revision is ignored. */
  const applyPreview = useCallback(async (preview: PlanPreview) => {
    const current = latest.current;
    if (current.status !== 'ready') return;
    if ((current.data.previewRevision ?? 0) > preview.preview_revision) return;
    const data = await withPreview(current.data, preview);
    setState({ data, status: 'ready' });
  }, []);

  return { applyPreview, reload, state };
}

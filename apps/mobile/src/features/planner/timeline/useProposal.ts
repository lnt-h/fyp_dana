import { useCallback, useEffect, useState } from 'react';
import { currentLocale } from '../../../i18n';
import { ApiError, getPlace, getPreview, getTrip, listCities } from '../../../lib/api/source';
import type { CityCode, Conflict, IsoDate, Media, PlanHealth, TripDetail, Uuid } from '../../../lib/api/types';
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
async function placesOf(days: NumberedDay[]): Promise<Record<Uuid, StopPlace>> {
  const ids = [...new Set(days.flatMap(day => day.stops.map(stop => stop.place_id)))];
  const entries = await Promise.all(ids.map(id => getPlace(id)
    .then(place => [id, { categoryCode: place.category_code, thumbnail: place.thumbnail }] as const)
    .catch(() => [id, { categoryCode: null, thumbnail: null }] as const)));
  return Object.fromEntries(entries);
}

function coverOf(days: NumberedDay[], places: Record<Uuid, StopPlace>): Media | null {
  const first = days.find(day => day.stops.length)?.stops[0];
  return first ? places[first.place_id]?.thumbnail ?? null : null;
}

async function fromTrip(trip: TripDetail): Promise<ProposalData> {
  const days = numberDays(trip.days);
  const [city, places] = await Promise.all([cityOf(trip.city_id), placesOf(days)]);
  return {
    ...city, cover: coverOf(days, places), days, health: null, healthReasons: [], places,
    readOnly: trip.status === 'SAVED', saved: trip.status === 'SAVED', startDate: trip.start_date,
  };
}

async function load({ previewId, tripId, mode }: Params): Promise<ProposalData> {
  // Saved trip opened from My trips: the saved itinerary, read-only (SCR-024 saved read mode).
  if (mode === 'saved' && tripId) return fromTrip(await getTrip(tripId));

  let preview;
  try {
    preview = await getPreview(previewId);
  } catch (error) {
    // No matching preview (e.g. previewId is the trip id): fall back to the trip's own itinerary.
    if (tripId && error instanceof ApiError && error.error.code === 'not_found') return fromTrip(await getTrip(tripId));
    throw error;
  }
  const days = numberDays(preview.days);
  const [trip, places] = await Promise.all([getTrip(preview.trip_id).catch(() => null), placesOf(days)]);
  return {
    ...(await cityOf(trip?.city_id)),
    cover: coverOf(days, places),
    days,
    places,
    health: preview.plan_health,
    healthReasons: preview.health_reasons ?? [],
    readOnly: preview.status !== 'ACTIVE',
    saved: preview.status === 'SAVED',
    startDate: trip?.start_date ?? null,
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

  return { reload, state };
}

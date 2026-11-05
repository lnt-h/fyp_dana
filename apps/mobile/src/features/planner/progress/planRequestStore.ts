import type { City, PlanPreviewCreate, Trip } from '../../../lib/api/types';

/** What SCR-023 needs to run the planning stream; set by SCR-022 just before navigating. In memory only. */
export type PlanRequest = {
  trip: Trip;
  city: City;
  body: PlanPreviewCreate;
};

let current: PlanRequest | null = null;

export const setPlanRequest = (request: PlanRequest) => { current = request; };
export const getPlanRequest = () => current;

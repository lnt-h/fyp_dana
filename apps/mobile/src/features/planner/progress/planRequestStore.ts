import { newIdempotencyKey } from '../../../lib/api/sourcePlanning';
import type { City, PlanPreviewCreate, Trip, Uuid } from '../../../lib/api/types';

/** What SCR-023 needs to run the planning stream; set by SCR-022 just before navigating. In memory only. */
export type PlanRequest = {
  trip: Trip;
  city: City;
  body: PlanPreviewCreate;
  /**
   * `Idempotency-Key` of this request. A retry after a dropped stream reuses it, so the server replays the preview it
   * already made (or reports it is still running) instead of creating a second one.
   */
  idempotencyKey: string;
};

let current: PlanRequest | null = null;
/** Previews this session already opened; a dropped stream never jumps to one of these (an older run of a reused trip). */
const seenPreviews = new Set<Uuid>();

export const setPlanRequest = (request: Omit<PlanRequest, 'idempotencyKey'>) => { current = { ...request, idempotencyKey: newIdempotencyKey() }; };
export const getPlanRequest = () => current;

/** A new attempt with a different outcome expected (e.g. after a server error): a fresh key. */
export function renewPlanRequestKey() {
  if (current) current = { ...current, idempotencyKey: newIdempotencyKey() };
}

export const markPreviewSeen = (previewId: Uuid) => { seenPreviews.add(previewId); };
export const isPreviewSeen = (previewId: Uuid) => seenPreviews.has(previewId);

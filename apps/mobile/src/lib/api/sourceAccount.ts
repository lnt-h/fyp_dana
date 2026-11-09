/**
 * Account calls (CMP-004): preferences (API-004/005) and account deletion (API-006/007). Always the Gonarra `/v1` API
 * (config.ts). Nothing here logs request bodies or tokens.
 */
import { apiRequest } from './client';
import { ApiError } from './errors';
import type { components } from './schema';
import type { Preferences } from './types';

type Schemas = components['schemas'];

export type PreferencesWrite = Schemas['PreferencesWrite'];
export type AccountDeletionStatus = Schemas['AccountDeletionStatus'];
export type DeletionState = AccountDeletionStatus['status'];

/** API-004 `GET /v1/me/preferences` (defaults when none were saved). */
export async function fetchPreferences(): Promise<Preferences> {
  return apiRequest<Preferences>('/v1/me/preferences');
}

/** API-005 `PUT /v1/me/preferences`: full replace, naturally idempotent. */
export async function savePreferences(body: PreferencesWrite): Promise<Preferences> {
  return apiRequest<Preferences>('/v1/me/preferences', { body, method: 'PUT' });
}

/** Contract `Preferences` → `PreferencesWrite` (drops server-stamped fields) so a partial change keeps the rest. */
export function toPreferencesWrite(current: Preferences, changes: Partial<PreferencesWrite> = {}): PreferencesWrite {
  return {
    allowed_modes: current.allowed_modes.length ? current.allowed_modes : ['WALK', 'DRIVE'],
    day_end_time: current.day_end_time ?? null,
    day_start_time: current.day_start_time ?? null,
    interest_category_codes: current.interest_category_codes,
    locale: current.locale,
    pace: current.pace ?? null,
    ...changes,
  };
}

/**
 * API-006 `POST /v1/me/deletion` `{confirm: true}` with an `Idempotency-Key` (reuse the same key when retrying). The
 * server also returns the open job when one is already REQUESTED or IN_PROGRESS.
 */
export async function requestAccountDeletion(idempotencyKey: string): Promise<AccountDeletionStatus> {
  return apiRequest<AccountDeletionStatus>('/v1/me/deletion', { body: { confirm: true }, idempotencyKey, method: 'POST' });
}

/**
 * API-007 `GET /v1/me/deletion`. Null when no deletion was requested (404). After the last step the Clerk user is gone
 * and the token is rejected: a client that saw the job running treats that 401 as COMPLETED (OQ-073), so it is
 * reported as `'gone'`.
 */
export async function getAccountDeletionStatus(): Promise<AccountDeletionStatus | null | 'gone'> {
  try {
    return await apiRequest<AccountDeletionStatus>('/v1/me/deletion');
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    if (error instanceof ApiError && error.status === 401) return 'gone';
    throw error;
  }
}

import type { TFunction } from 'i18next';

const knownCodes = [
  'network', 'route_unavailable', 'ai_unavailable', 'revision_conflict', 'preview_expired', 'preview_closed', 'validation_error',
  'place_not_in_city', 'quota_exceeded', 'idempotency_in_progress', 'database_unavailable', 'resource_not_found', 'authentication_required', 'internal_error',
  'unsupported_request', 'trip_not_saved', 'day_overflow', 'publication_incomplete', 'duplicate_place', 'unknown_stop', 'unknown_leg',
  'not_published', 'idempotency_key_reused', 'snapshot_invalid', 'plan_blocked', 'stop_locked',
] as const;
type KnownCode = typeof knownCodes[number];

/** S-1: error `code` → localized copy (never provider text). Unknown codes fall back to `internal_error`. */
export function editErrorCopy(t: TFunction, code: string | undefined): string {
  const known: KnownCode = code && (knownCodes as readonly string[]).includes(code) ? code as KnownCode : 'internal_error';
  return t(`proposal.errors.${known}`);
}

/** True when the same request can never succeed (non-retryable 4xx): offer Discard, not Retry. */
export const isRejected = (status: string | undefined) => status === 'rejected';

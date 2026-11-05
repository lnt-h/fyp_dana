import type { TFunction } from 'i18next';

const knownCodes = [
  'network', 'route_unavailable', 'ai_unavailable', 'revision_conflict', 'preview_expired', 'preview_closed', 'validation_failed',
  'place_not_in_city', 'quota_exceeded', 'idempotency_in_progress', 'database_unavailable', 'not_found', 'internal_error',
] as const;
type KnownCode = typeof knownCodes[number];

/** S-1: error `code` → localized copy (never provider text). Unknown codes fall back to `internal_error`. */
export function editErrorCopy(t: TFunction, code: string | undefined): string {
  const known: KnownCode = code && (knownCodes as readonly string[]).includes(code) ? code as KnownCode : 'internal_error';
  return t(`proposal.errors.${known}`);
}

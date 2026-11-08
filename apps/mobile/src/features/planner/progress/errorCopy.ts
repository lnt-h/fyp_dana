import type { TFunction } from 'i18next';
import { ApiError } from '../../../lib/api/source';
import type { ErrorDetail } from '../../../lib/api/types';

const knownCodes = [
  'ai_unavailable', 'route_unavailable', 'quota_exceeded', 'validation_error', 'unsupported_request', 'resource_not_found', 'authentication_required',
  'preview_expired', 'preview_closed', 'database_unavailable', 'network', 'internal_error', 'revision_conflict', 'trip_not_saved',
] as const;
type KnownCode = typeof knownCodes[number];

/** Normalises anything thrown by the data source into a Gonarra error detail (S-1); never exposes provider text. */
export function toErrorDetail(error: unknown): ErrorDetail {
  if (error instanceof ApiError) return error.error;
  if (error instanceof TypeError) return { code: 'network', message: '', retryable: true };
  return { code: 'internal_error', message: '', retryable: true };
}

/** S-1 copy for an error code; unknown codes fall back to the generic message. */
export function errorCopy(t: TFunction, code: string): string {
  const known: KnownCode = (knownCodes as readonly string[]).includes(code) ? code as KnownCode : 'internal_error';
  return t(`planner.errors.codes.${known}`);
}

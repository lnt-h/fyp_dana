import type { ErrorDetail } from './types';

/**
 * Thrown for a non-2xx response; `error` is the Gonarra envelope body `{error:{code,message,retryable,request_id,context}}`
 * (map `error.code` to copy, S-1). Network failures are not ApiErrors: `fetch` rejects with a `TypeError`.
 */
export class ApiError extends Error {
  constructor(public readonly error: ErrorDetail, public readonly status: number) {
    super(error.code);
    this.name = 'ApiError';
  }

  get code(): string {
    return this.error.code;
  }

  get retryable(): boolean {
    return this.error.retryable ?? false;
  }

  get requestId(): string | null {
    return this.error.request_id ?? null;
  }
}

const isObject = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null;

/**
 * Contract 1.0 error codes (openapi.yaml responses): 401 `authentication_required`, 404 `resource_not_found`, 422
 * `validation_error`. Pre-1.0 servers sent the left-hand names; they are normalised so screens match one code each.
 */
const LEGACY_CODES: Record<string, string> = {
  not_found: 'resource_not_found',
  unauthorized: 'authentication_required',
  validation_failed: 'validation_error',
};

export const normalizeErrorCode = (code: string): string => LEGACY_CODES[code] ?? code;

/** Parses an `ErrorResponse` body; null when the body is not the Gonarra envelope. */
export function parseErrorEnvelope(body: unknown): ErrorDetail | null {
  if (!isObject(body) || !isObject(body.error)) return null;
  const { code, message, retryable, request_id, context } = body.error;
  if (typeof code !== 'string') return null;
  return {
    code: normalizeErrorCode(code),
    context: isObject(context) ? context : undefined,
    message: typeof message === 'string' ? message : '',
    request_id: typeof request_id === 'string' ? request_id : null,
    retryable: typeof retryable === 'boolean' ? retryable : false,
  };
}

/** Error for a response without a usable envelope (proxy page, empty body). 5xx and 429 count as retryable. */
export function fallbackError(status: number, requestId: string | null): ErrorDetail {
  const code = status === 401 ? 'authentication_required' : status === 404 ? 'resource_not_found' : status === 422 ? 'validation_error' : status === 429 ? 'quota_exceeded' : status >= 500 ? 'internal_error' : 'bad_request';
  return { code, message: '', request_id: requestId, retryable: status >= 500 || status === 429 };
}

/** True for a 401 / `authentication_required` response: the Clerk session is missing or expired. */
export function isAuthError(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 401 || error.code === 'authentication_required');
}

/**
 * Why a screen could not load, for the retry banner's second line: `offline` = the request never reached the server
 * (fetch rejects with `TypeError`); `auth` = 401 `authentication_required` (session expired; offer "Sign in again",
 * `common.signInAgain`); `busy` = quota or a dependency is down (429, 502–504, `*_unavailable`), worth a retry later;
 * `server` = any other error response.
 */
export type LoadErrorKind = 'offline' | 'auth' | 'busy' | 'server';

export function loadErrorKind(error: unknown): LoadErrorKind {
  if (isAuthError(error)) return 'auth';
  if (error instanceof ApiError) {
    const busy = error.status === 429 || error.status === 502 || error.status === 503 || error.status === 504
      || error.code === 'quota_exceeded' || error.code.endsWith('_unavailable');
    return busy ? 'busy' : 'server';
  }
  return error instanceof TypeError ? 'offline' : 'server';
}

/** Route that resolves an `auth` load error: the sign-in screen (the session is gone, so sign in again). */
export const SIGN_IN_AGAIN_ROUTE = '/login' as const;

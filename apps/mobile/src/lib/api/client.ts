/**
 * Typed HTTP client for the Gonarra `/v1` contract (docs/04-design/api/openapi.yaml; generated types in `schema.d.ts`,
 * regenerate with `npm run gen:api`). Every request carries:
 * - `Authorization: Bearer <Clerk session JWT>` when signed in (ADR-005; token from `ApiAuthBridge`),
 * - `X-Request-ID` (fresh UUID, echoed by the server and in error envelopes),
 * - `Accept-Language` (current app locale, `vi` or `en`),
 * - `Idempotency-Key` when the caller passes one (mutating planning/Save calls; reuse the key on retry).
 * Non-2xx responses throw `ApiError` with the parsed envelope; a lost connection rejects with `TypeError` (fetch).
 * Nothing here logs tokens, request bodies or locations.
 */
import * as Crypto from 'expo-crypto';

import { currentLocale } from '../../i18n';
import { getAuthToken } from './auth';
import { API_BASE_URL } from './config';
import { ApiError, fallbackError, parseErrorEnvelope } from './errors';

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export type QueryValue = string | number | boolean | null | undefined;

export type RequestOptions = {
  method?: HttpMethod;
  query?: Record<string, QueryValue>;
  /** JSON body (serialised here). */
  body?: unknown;
  /** Sent as `Idempotency-Key`; required by the contract on replayable mutations. */
  idempotencyKey?: string;
  accept?: string;
  signal?: AbortSignal;
};

export const newRequestId = (): string => Crypto.randomUUID();

/** Absolute URL for a `/v1/...` path plus query (null/undefined values are dropped). */
export function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const params = Object.entries(query ?? {})
    .filter((entry): entry is [string, string | number | boolean] => entry[1] !== null && entry[1] !== undefined && entry[1] !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
  return `${API_BASE_URL}${path}${params.length ? `?${params.join('&')}` : ''}`;
}

/** Headers shared by JSON and SSE requests. */
export async function buildHeaders(options: Pick<RequestOptions, 'body' | 'idempotencyKey' | 'accept'>): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    Accept: options.accept ?? 'application/json',
    'Accept-Language': currentLocale(),
    'X-Request-ID': newRequestId(),
  };
  const token = await getAuthToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  if (options.idempotencyKey) headers['Idempotency-Key'] = options.idempotencyKey;
  return headers;
}

/** Minimal response surface shared by global fetch and expo/fetch. */
type ResponseLike = { status: number; ok: boolean; headers: { get(name: string): string | null }; text(): Promise<string> };

/** Throws `ApiError` for a non-2xx response, parsing the shared envelope when present. */
export async function throwIfNotOk(response: ResponseLike): Promise<void> {
  if (response.ok) return;
  const requestId = response.headers.get('X-Request-ID');
  let detail = null;
  try {
    const text = await response.text();
    detail = text ? parseErrorEnvelope(JSON.parse(text)) : null;
  } catch {
    detail = null;
  }
  throw new ApiError(detail ? { ...detail, request_id: detail.request_id ?? requestId } : fallbackError(response.status, requestId), response.status);
}

export type ApiResponse<T> = { data: T; status: number; headers: { get(name: string): string | null } };

/** One JSON request; resolves with the parsed body (undefined for 204) plus status and headers. */
export async function apiRequestRaw<T>(path: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
  const response = await fetch(buildUrl(path, options.query), {
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    headers: await buildHeaders(options),
    method: options.method ?? 'GET',
    signal: options.signal,
  });
  await throwIfNotOk(response);
  const text = response.status === 204 ? '' : await response.text();
  return { data: (text ? JSON.parse(text) : undefined) as T, headers: response.headers, status: response.status };
}

/** One JSON request; resolves with the parsed body. */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return (await apiRequestRaw<T>(path, options)).data;
}

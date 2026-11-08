/**
 * API configuration. `EXPO_PUBLIC_API_URL` is REQUIRED (e.g. `http://192.168.1.20:8000`, no trailing `/v1`): every data
 * source (`source*.ts`) calls the Gonarra `/v1` API. There is no local/demo data fallback; when the variable is missing
 * or invalid the root layout shows a configuration-error screen instead of the app (`isApiConfigured()`).
 *
 * Expo inlines `process.env.EXPO_PUBLIC_*` at build time, so the value is fixed per bundle; restart Metro after a change.
 */
const rawApiUrl = (process.env.EXPO_PUBLIC_API_URL ?? '').trim();

/** Base URL without a trailing slash; paths passed to the client start with `/v1/…`. Empty when not configured. */
export const API_BASE_URL = rawApiUrl.replace(/\/+$/, '');

/** True when `EXPO_PUBLIC_API_URL` is an absolute http(s) URL. False → the root layout renders the configuration error. */
export function isApiConfigured(): boolean {
  return /^https?:\/\/[^/\s]+/i.test(API_BASE_URL);
}

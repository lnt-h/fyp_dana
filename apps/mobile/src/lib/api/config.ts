/**
 * Remote/fixture switch for every data source (`source*.ts`).
 *
 * - `EXPO_PUBLIC_API_URL` set (e.g. `http://192.168.1.20:8000`, no trailing `/v1`) → calls go to the Gonarra API.
 * - `EXPO_PUBLIC_API_URL` unset or empty → every call is served from local fixtures (src/lib/api/fixtures, not catalog
 *   data). This is the default so the app runs with no backend.
 * - `EXPO_PUBLIC_USE_FIXTURES=1` forces fixtures even when an API URL is set (handy for UI work against a live .env).
 *
 * Expo inlines `process.env.EXPO_PUBLIC_*` at build time, so the switch is fixed per bundle; restart Metro after a change.
 */
const rawApiUrl = (process.env.EXPO_PUBLIC_API_URL ?? '').trim();

/** Base URL without a trailing slash; paths passed to the client start with `/v1/…`. Empty in fixture mode. */
export const API_BASE_URL = rawApiUrl.replace(/\/+$/, '');

const forceFixtures = process.env.EXPO_PUBLIC_USE_FIXTURES === '1';

/** True when data sources call the real API; false when they serve fixtures. */
export function isRemoteEnabled(): boolean {
  return API_BASE_URL.length > 0 && !forceFixtures;
}

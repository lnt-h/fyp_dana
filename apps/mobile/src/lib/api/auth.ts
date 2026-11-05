/**
 * Bridge from Clerk (React context) to the plain-function API client. `ApiAuthBridge` (rendered inside `ClerkProvider`)
 * registers `useAuth().getToken`; the client calls `getAuthToken()` before every request. The token is never logged
 * or persisted by the client.
 */
type TokenGetter = () => Promise<string | null>;

let getter: TokenGetter | null = null;

export function setAuthTokenGetter(next: TokenGetter | null): void {
  getter = next;
}

/** The current Clerk session JWT, or null when signed out or before Clerk has loaded. */
export async function getAuthToken(): Promise<string | null> {
  if (!getter) return null;
  try {
    return await getter();
  } catch {
    return null;
  }
}

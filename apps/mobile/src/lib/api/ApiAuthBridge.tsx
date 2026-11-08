import { useAuth } from '@clerk/expo';
import { useEffect } from 'react';

import { demoNoAuth } from '../demoAuth';
import { setAuthTokenGetter } from './auth';

/** Renders nothing (and registers no getter in demo mode, see demoAuth.ts); keeps the API client's token getter pointed at the live Clerk session. Mount inside ClerkProvider. */
export function ApiAuthBridge() {
  const { getToken, isSignedIn } = useAuth();
  useEffect(() => {
    // Demo mode: no token getter, so requests carry no Authorization header (API demo shared user).
    setAuthTokenGetter(!demoNoAuth && isSignedIn ? () => getToken() : null);
    return () => setAuthTokenGetter(null);
  }, [getToken, isSignedIn]);
  return null;
}

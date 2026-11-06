import { useAuth } from '@clerk/expo';
import { useEffect } from 'react';

import { setAuthTokenGetter } from './auth';

/** Renders nothing; keeps the API client's token getter pointed at the live Clerk session. Mount inside ClerkProvider. */
export function ApiAuthBridge() {
  const { getToken, isSignedIn } = useAuth();
  useEffect(() => {
    setAuthTokenGetter(isSignedIn ? () => getToken() : null);
    return () => setAuthTokenGetter(null);
  }, [getToken, isSignedIn]);
  return null;
}

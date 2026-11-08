/**
 * Demo mode (`EXPO_PUBLIC_DEMO_NO_AUTH=1`): anyone who opens the build is treated as signed in as one shared demo user,
 * with no Clerk session and no Authorization header (the API must run with GONARRA_DEMO_SHARED_USER). Off by default;
 * never enable it for a real release. `AccountContext` is the single source of `isSignedIn` for the rest of the app.
 */
export const demoNoAuth = process.env.EXPO_PUBLIC_DEMO_NO_AUTH === '1';

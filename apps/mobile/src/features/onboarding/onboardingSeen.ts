import * as SecureStore from 'expo-secure-store';

/** Device flag: the guest has finished or skipped onboarding once, so cold starts go straight to Home. */
const KEY = 'gonarra.onboardingSeen';

export async function hasSeenOnboarding(): Promise<boolean> {
  try {
    return (await SecureStore.getItemAsync(KEY)) === '1';
  } catch {
    return false;
  }
}

export function markOnboardingSeen(): void {
  SecureStore.setItemAsync(KEY, '1').catch(() => undefined);
}

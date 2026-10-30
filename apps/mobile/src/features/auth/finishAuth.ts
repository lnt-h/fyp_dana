import type { SetActiveNavigate } from '@clerk/shared/types';
import { router } from 'expo-router';
import { Platform } from 'react-native';

export function authDestination(destination: '/home' | '/travel-preferences'): SetActiveNavigate {
  return async ({ session, decorateUrl }) => {
    const target = session?.currentTask ? '/auth-task' : destination;
    const url = decorateUrl(target);
    if (Platform.OS === 'web' && /^https?:\/\//.test(url)) {
      window.location.assign(url);
    } else {
      router.replace(target);
    }
  };
}

export const finishAuth = authDestination('/home');

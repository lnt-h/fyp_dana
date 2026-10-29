import { useEffect, useState } from 'react';
import { AccessibilityInfo } from 'react-native';
import { useAccount } from '../features/account/AccountContext';

export function useReducedMotion() {
  const { reduceMotion } = useAccount();
  const [isReducedMotionEnabled, setIsReducedMotionEnabled] = useState(false);

  useEffect(() => {
    let isMounted = true;

    void AccessibilityInfo.isReduceMotionEnabled()
      .then((enabled) => {
        if (isMounted) {
          setIsReducedMotionEnabled(enabled);
        }
      })
      .catch(() => undefined);

    const subscription = AccessibilityInfo.addEventListener(
      'reduceMotionChanged',
      setIsReducedMotionEnabled,
    );

    return () => {
      isMounted = false;
      subscription.remove();
    };
  }, []);

  return isReducedMotionEnabled || reduceMotion;
}

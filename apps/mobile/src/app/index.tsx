import { useEffect } from 'react';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useAccount } from '../features/account/AccountContext';
import { hasSeenOnboarding } from '../features/onboarding/onboardingSeen';
import { LoadingDots, SplashLogo } from '../components/brand/BrandMarks';
import { colors } from '../theme/colors';

/** Splash: signed-in travellers and returning guests (onboarding seen on this device) go to Home; first-time guests see onboarding. */
export default function SplashScreen() {
  const { isLoaded, isSignedIn } = useAccount();
  const insets = useSafeAreaInsets();

  useEffect(() => {
    if (!isLoaded) return;
    if (isSignedIn) { router.replace('/home'); return; }
    let alive = true;
    hasSeenOnboarding().then(seen => { if (alive) router.replace(seen ? '/home' : '/onboarding'); });
    return () => { alive = false; };
  }, [isLoaded, isSignedIn]);

  return (
    <View style={styles.screen}>
      <StatusBar style="light" />

      <View accessibilityLabel="Gonarra" style={styles.logo}>
        <SplashLogo />
      </View>

      <View style={[styles.loading, { bottom: insets.bottom + 54 }]}>
        <LoadingDots />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    alignItems: 'center',
    backgroundColor: colors.deepOcean,
    flex: 1,
    justifyContent: 'center',
  },
  logo: {
    height: 99,
    width: 79,
  },
  loading: {
    alignItems: 'center',
    justifyContent: 'center',
    height: 36,
    position: 'absolute',
    width: 36,
  },
});

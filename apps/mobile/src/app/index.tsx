import { useEffect } from 'react';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  LOADING_CYCLE_DURATION_MS,
  LoadingDots,
  SplashLogo,
} from '../components/brand/BrandMarks';
import { colors } from '../theme/colors';

const SPLASH_CYCLE_COUNT = 2;
const SPLASH_DURATION_MS = LOADING_CYCLE_DURATION_MS * SPLASH_CYCLE_COUNT;

export default function SplashScreen() {
  const insets = useSafeAreaInsets();

  useEffect(() => {
    const timer = setTimeout(() => router.replace('/onboarding'), SPLASH_DURATION_MS);

    return () => clearTimeout(timer);
  }, []);

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

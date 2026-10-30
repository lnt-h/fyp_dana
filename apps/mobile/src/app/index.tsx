import { useEffect } from 'react';
import { useAuth } from '@clerk/expo';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { LoadingDots, SplashLogo } from '../components/brand/BrandMarks';
import { colors } from '../theme/colors';

export default function SplashScreen() {
  const { isLoaded, isSignedIn } = useAuth();
  const insets = useSafeAreaInsets();

  useEffect(() => {
    if (isLoaded) router.replace(isSignedIn ? '/home' : '/onboarding');
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

import { useCallback } from 'react';
import { StatusBar } from 'expo-status-bar';
import {
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Wordmark } from '../components/brand/BrandMarks';
import { OnboardingMosaic } from '../features/onboarding/components/OnboardingMosaic';
import { colors } from '../theme/colors';

export default function OnboardingScreen() {
  const { height, width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const buttonBottom = Math.max(insets.bottom, 12) + 14;

  const handleNext = useCallback(() => {
    // The next onboarding route will be connected with the next product slice.
  }, []);

  const handleSkip = useCallback(() => {
    // The authenticated/home route is intentionally outside this two-screen slice.
  }, []);

  return (
    <View style={styles.screen}>
      <StatusBar style="dark" />
      <OnboardingMosaic height={height} width={width} />

      <View style={[styles.header, { top: insets.top + 10 }]}>
        <Wordmark />
        <Pressable
          accessibilityHint="Skip the onboarding introduction"
          accessibilityRole="button"
          hitSlop={12}
          onPress={handleSkip}
          style={({ pressed }) => [styles.skipButton, pressed && styles.pressed]}
        >
          <Text style={styles.skipText}>Skip</Text>
        </Pressable>
      </View>

      <View style={[styles.copyBlock, { bottom: buttonBottom + 184 }]}>
        <Text style={styles.title}>Discover Da Nang’s{`\n`}stories, anytime,{`\n`}at any stop!</Text>
      </View>

      <View style={[styles.pagination, { bottom: buttonBottom + 86 }]}>
        <View style={[styles.pageDot, styles.pageDotActive]} />
        <View style={styles.pageDot} />
        <View style={styles.pageDot} />
      </View>

      <Pressable
        accessibilityHint="Continue to the next onboarding step"
        accessibilityRole="button"
        onPress={handleNext}
        style={({ pressed }) => [
          styles.nextButton,
          { bottom: buttonBottom, width: width - 32 },
          pressed && styles.nextButtonPressed,
        ]}
      >
        <Text style={styles.nextText}>Next</Text>
        <Text accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.arrow}>
          →
        </Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: colors.white,
    flex: 1,
    overflow: 'hidden',
  },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    left: 16,
    position: 'absolute',
    right: 16,
    zIndex: 4,
  },
  skipButton: {
    alignItems: 'center',
    borderRadius: 20,
    height: 40,
    justifyContent: 'center',
    minWidth: 64,
  },
  skipText: {
    color: colors.deepOcean,
    fontSize: 16,
    fontWeight: '600',
    lineHeight: 22,
  },
  pressed: {
    backgroundColor: colors.skyWash,
  },
  copyBlock: {
    alignItems: 'center',
    left: 16,
    position: 'absolute',
    right: 16,
    zIndex: 3,
  },
  title: {
    color: colors.deepOcean,
    fontSize: 30,
    fontWeight: '700',
    letterSpacing: -0.8,
    lineHeight: 31,
    textAlign: 'center',
  },
  pagination: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 4,
    justifyContent: 'center',
    left: 0,
    position: 'absolute',
    right: 0,
    zIndex: 3,
  },
  pageDot: {
    backgroundColor: colors.mutedDot,
    borderRadius: 4,
    height: 8,
    width: 8,
  },
  pageDotActive: {
    backgroundColor: colors.deepOcean,
    width: 28,
  },
  nextButton: {
    alignItems: 'center',
    alignSelf: 'center',
    backgroundColor: colors.ink,
    borderRadius: 30,
    flexDirection: 'row',
    height: 60,
    justifyContent: 'center',
    left: 16,
    position: 'absolute',
    zIndex: 4,
  },
  nextButtonPressed: {
    opacity: 0.82,
    transform: [{ scale: 0.99 }],
  },
  nextText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '700',
    lineHeight: 22,
  },
  arrow: {
    color: colors.white,
    fontSize: 18,
    lineHeight: 22,
    marginLeft: 8,
  },
});

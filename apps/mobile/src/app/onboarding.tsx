import { useCallback, useRef, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import {
  Animated,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';

import { Wordmark } from '../components/brand/BrandMarks';
import { OnboardingMosaic } from '../features/onboarding/components/OnboardingMosaic';
import { PlanningOnboardingScene } from '../features/onboarding/components/PlanningOnboardingScene';
import { colors } from '../theme/colors';

const slides = [
  {
    key: 'discover',
    title: 'Discover Da Nang’s\nstories, anytime,\nat any stop!',
  },
  {
    key: 'plan',
    title: 'Pin what you love, plan\nyour day, let the city\nsurprise you!',
  },
] as const;

const lastSlideIndex = slides.length - 1;

function DirectionIcon({ direction }: { direction: 'back' | 'next' }) {
  const path = direction === 'back' ? 'M15 5L7 13L15 21' : 'M9 5L17 13L9 21';

  return (
    <Svg height={26} viewBox="0 0 24 26" width={24}>
      <Path
        d={path}
        fill="none"
        stroke={colors.white}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
      />
    </Svg>
  );
}

export default function OnboardingScreen() {
  const { height, width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const [slideIndex, setSlideIndex] = useState(0);
  const opacity = useRef(new Animated.Value(1)).current;
  const translateX = useRef(new Animated.Value(0)).current;
  const isAnimating = useRef(false);
  const useNativeDriver = Platform.OS !== 'web';

  const buttonBottom = Math.max(insets.bottom, 34);
  const titleFontSize = Math.min(37, width * 0.084);
  const slide = slides[slideIndex];

  const changeSlide = useCallback(
    (nextIndex: number, direction: -1 | 1) => {
      if (nextIndex < 0 || nextIndex > lastSlideIndex || isAnimating.current) {
        return;
      }

      isAnimating.current = true;
      Animated.parallel([
        Animated.timing(opacity, {
          duration: 110,
          toValue: 0,
          useNativeDriver,
        }),
        Animated.timing(translateX, {
          duration: 110,
          toValue: direction * -14,
          useNativeDriver,
        }),
      ]).start(({ finished }) => {
        if (!finished) {
          isAnimating.current = false;
          return;
        }

        setSlideIndex(nextIndex);
        translateX.setValue(direction * 18);

        Animated.parallel([
          Animated.timing(opacity, {
            duration: 220,
            toValue: 1,
            useNativeDriver,
          }),
          Animated.timing(translateX, {
            duration: 220,
            toValue: 0,
            useNativeDriver,
          }),
        ]).start(() => {
          isAnimating.current = false;
        });
      });
    },
    [opacity, translateX, useNativeDriver],
  );

  const handleNext = useCallback(() => {
    if (slideIndex < lastSlideIndex) {
      changeSlide(slideIndex + 1, 1);
    }
  }, [changeSlide, slideIndex]);

  const handleBack = useCallback(() => {
    if (slideIndex > 0) {
      changeSlide(slideIndex - 1, -1);
    }
  }, [changeSlide, slideIndex]);

  const handleSkip = useCallback(() => {
    // The home experience will own onboarding completion in the next product slice.
  }, []);

  return (
    <View style={styles.screen}>
      <StatusBar style="dark" />

      <Animated.View
        style={[
          StyleSheet.absoluteFill,
          {
            opacity,
            transform: [{ translateX }],
          },
        ]}
      >
        {slide.key === 'discover' ? (
          <OnboardingMosaic height={height} width={width} />
        ) : (
          <PlanningOnboardingScene height={height} width={width} />
        )}

        <View style={[styles.copyBlock, { bottom: buttonBottom + 174 }]}>
          <Text
            style={[
              styles.title,
              {
                fontSize: titleFontSize,
                lineHeight: titleFontSize + 1,
              },
            ]}
          >
            {slide.title}
          </Text>
        </View>
      </Animated.View>

      <View style={[styles.header, { top: insets.top + 10 }]}>
        <Wordmark />
        <Pressable
          accessibilityHint="Skip the onboarding introduction"
          accessibilityLabel="Skip onboarding"
          accessibilityRole="button"
          hitSlop={12}
          onPress={handleSkip}
          style={({ pressed }) => [styles.skipButton, pressed && styles.pressed]}
        >
          <Text style={styles.skipText}>Skip</Text>
        </Pressable>
      </View>

      <View style={[styles.pagination, { bottom: buttonBottom + 90 }]}>
        {slides.map((item, index) => (
          <View
            accessibilityLabel={`Onboarding page ${index + 1} of ${slides.length}`}
            key={item.key}
            style={[styles.pageDot, index === slideIndex && styles.pageDotActive]}
          />
        ))}
        <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.pageDot} />
      </View>

      <View
        style={[
          styles.footer,
          {
            bottom: buttonBottom,
            left: slideIndex === 0 ? 16 : 22,
            right: slideIndex === 0 ? 16 : 21,
          },
        ]}
      >
        {slideIndex > 0 ? (
          <Pressable
            accessibilityHint="Return to the previous onboarding step"
            accessibilityLabel="Previous onboarding step"
            accessibilityRole="button"
            onPress={handleBack}
            style={({ pressed }) => [styles.backButton, pressed && styles.backButtonPressed]}
          >
            <DirectionIcon direction="back" />
          </Pressable>
        ) : null}

        <Pressable
          accessibilityHint={
            slideIndex < lastSlideIndex
              ? 'Continue to the next onboarding step'
              : 'Continue when the next onboarding step is available'
          }
          accessibilityLabel="Next onboarding step"
          accessibilityRole="button"
          onPress={handleNext}
          style={({ pressed }) => [styles.nextButton, pressed && styles.nextButtonPressed]}
        >
          <Text style={styles.nextText}>Next</Text>
          <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.nextIcon}>
            <DirectionIcon direction="next" />
          </View>
        </Pressable>
      </View>
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
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 20,
    height: 40,
    justifyContent: 'center',
    minWidth: 88,
  },
  skipText: {
    color: colors.deepOcean,
    fontSize: 20,
    fontWeight: '700',
    lineHeight: 24,
  },
  pressed: {
    backgroundColor: 'rgba(255,255,255,0.6)',
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
    fontWeight: '500',
    letterSpacing: -1.35,
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
    zIndex: 4,
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
  footer: {
    flexDirection: 'row',
    gap: 15,
    height: 60,
    position: 'absolute',
    zIndex: 4,
  },
  backButton: {
    alignItems: 'center',
    backgroundColor: '#B8C0C4',
    borderRadius: 30,
    height: 60,
    justifyContent: 'center',
    width: 60,
  },
  backButtonPressed: {
    backgroundColor: '#A7B0B5',
    transform: [{ scale: 0.98 }],
  },
  nextButton: {
    alignItems: 'center',
    backgroundColor: colors.ink,
    borderRadius: 30,
    flex: 1,
    flexDirection: 'row',
    height: 60,
    justifyContent: 'center',
  },
  nextButtonPressed: {
    opacity: 0.82,
    transform: [{ scale: 0.99 }],
  },
  nextText: {
    color: colors.white,
    fontSize: 20,
    fontWeight: '700',
    lineHeight: 24,
  },
  nextIcon: {
    marginLeft: 6,
    transform: [{ scale: 0.58 }],
  },
});

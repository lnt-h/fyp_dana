import { useCallback, useEffect, useRef, useState } from 'react';
import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import {
  Animated,
  Easing,
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
import { useReducedMotion } from '../hooks/useReducedMotion';
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

const designFrame = {
  height: 956,
  width: 440,
} as const;

const slideTransition = {
  duration: 260,
  offset: 24,
} as const;

type SlideCopyProps = {
  bottom: number;
  fontSize: number;
  title: string;
};

function SlideCopy({ bottom, fontSize, title }: SlideCopyProps) {
  return (
    <View style={[styles.copyBlock, { bottom }]}>
      <Text style={[styles.title, { fontSize, lineHeight: fontSize + 1 }]}>{title}</Text>
    </View>
  );
}

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
  const [planningPrepared, setPlanningPrepared] = useState(false);
  const transitionProgress = useRef(new Animated.Value(0)).current;
  const scheduledFrame = useRef<number | null>(null);
  const isAnimating = useRef(false);
  const reducedMotionEnabled = useReducedMotion();
  const useNativeDriver = Platform.OS !== 'web';

  const slide = slides[slideIndex];
  const designScale = Math.min(width / designFrame.width, height / designFrame.height);
  const buttonBottom = Math.max(insets.bottom, 34);
  const horizontalPadding = 16 * designScale;
  const headerTop = Math.max(insets.top + 8 * designScale, 72 * designScale);
  const wordmarkWidth = 133 * designScale;
  const headerFadeHeight = (slide.key === 'discover' ? 202 : 184) * designScale;
  const titleFontSize = Math.min(37, width * 0.084);
  const copyBottom = buttonBottom + 174;
  const transitionOffset = slideTransition.offset * designScale;

  useEffect(() => {
    const preparationTask = requestIdleCallback(() => {
      setPlanningPrepared(true);
    }, { timeout: 500 });

    return () => {
      cancelIdleCallback(preparationTask);
      transitionProgress.stopAnimation();

      if (scheduledFrame.current !== null) {
        cancelAnimationFrame(scheduledFrame.current);
      }
    };
  }, [transitionProgress]);

  const changeSlide = useCallback(
    (nextIndex: number) => {
      if (nextIndex < 0 || nextIndex > lastSlideIndex || isAnimating.current) {
        return;
      }

      isAnimating.current = true;
      const runTransition = () => {
        setSlideIndex(nextIndex);
        Animated.timing(transitionProgress, {
          duration: reducedMotionEnabled ? 0 : slideTransition.duration,
          easing: Easing.out(Easing.cubic),
          toValue: nextIndex,
          useNativeDriver,
        }).start(() => {
          isAnimating.current = false;
        });
      };

      if (nextIndex === 1 && !planningPrepared) {
        setPlanningPrepared(true);
        scheduledFrame.current = requestAnimationFrame(() => {
          scheduledFrame.current = null;
          runTransition();
        });
        return;
      }

      runTransition();
    },
    [planningPrepared, reducedMotionEnabled, transitionProgress, useNativeDriver],
  );

  const handleNext = useCallback(() => {
    if (slideIndex < lastSlideIndex) {
      changeSlide(slideIndex + 1);
    }
  }, [changeSlide, slideIndex]);

  const handleBack = useCallback(() => {
    if (slideIndex > 0) {
      changeSlide(slideIndex - 1);
    }
  }, [changeSlide, slideIndex]);

  const handleSkip = useCallback(() => {
    // The home experience will own onboarding completion in the next product slice.
  }, []);

  return (
    <View style={styles.screen}>
      <StatusBar style="dark" />

      <Animated.View
        accessibilityElementsHidden={slideIndex !== 0}
        importantForAccessibility={slideIndex === 0 ? 'auto' : 'no-hide-descendants'}
        pointerEvents="none"
        style={[
          styles.slideLayer,
          {
            opacity: transitionProgress.interpolate({
              inputRange: [0, 1],
              outputRange: [1, 0],
            }),
            transform: [
              {
                translateX: transitionProgress.interpolate({
                  inputRange: [0, 1],
                  outputRange: [0, -transitionOffset],
                }),
              },
            ],
          },
        ]}
      >
        <OnboardingMosaic height={height} width={width} />
        <SlideCopy bottom={copyBottom} fontSize={titleFontSize} title={slides[0].title} />
      </Animated.View>

      {planningPrepared ? (
        <Animated.View
          accessibilityElementsHidden={slideIndex !== 1}
          importantForAccessibility={slideIndex === 1 ? 'auto' : 'no-hide-descendants'}
          pointerEvents="none"
          style={[
            styles.slideLayer,
            {
              opacity: transitionProgress,
              transform: [
                {
                  translateX: transitionProgress.interpolate({
                    inputRange: [0, 1],
                    outputRange: [transitionOffset, 0],
                  }),
                },
              ],
            },
          ]}
        >
          <PlanningOnboardingScene height={height} width={width} />
          <SlideCopy bottom={copyBottom} fontSize={titleFontSize} title={slides[1].title} />
        </Animated.View>
      ) : null}

      <LinearGradient
        colors={[colors.white, 'rgba(255,255,255,0.5)', 'rgba(255,255,255,0)']}
        locations={slide.key === 'discover' ? [0.4426653, 0.7473981, 1] : [0.3656812, 0.7950298, 1]}
        pointerEvents="none"
        style={[styles.headerFade, { height: headerFadeHeight }]}
      />

      <View style={[styles.header, { left: horizontalPadding, right: horizontalPadding, top: headerTop }]}>
        <Wordmark width={wordmarkWidth} />
        <Pressable
          accessibilityHint="Skip the onboarding introduction"
          accessibilityLabel="Skip onboarding"
          accessibilityRole="button"
          hitSlop={12}
          onPress={handleSkip}
          style={({ pressed }) => [
            styles.skipButton,
            {
              borderRadius: 20 * designScale,
              height: 40 * designScale,
              width: 88 * designScale,
            },
            pressed && styles.pressed,
          ]}
        >
          <Text
            style={[
              styles.skipText,
              {
                fontSize: 20 * designScale,
                lineHeight: 22 * designScale,
              },
            ]}
          >
            Skip
          </Text>
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
  slideLayer: {
    bottom: 0,
    left: 0,
    position: 'absolute',
    right: 0,
    top: 0,
  },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    position: 'absolute',
    zIndex: 4,
  },
  headerFade: {
    left: 0,
    position: 'absolute',
    right: 0,
    top: 0,
    zIndex: 3,
  },
  skipButton: {
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
  },
  skipText: {
    color: colors.deepOcean,
    fontWeight: '700',
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

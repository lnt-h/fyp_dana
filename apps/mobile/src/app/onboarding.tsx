import { useCallback, useEffect, useRef, useState } from 'react';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
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
import { useTranslation } from 'react-i18next';
import Svg, { Path } from 'react-native-svg';

import { Wordmark } from '../components/brand/BrandMarks';
import { OnboardingMosaic } from '../features/onboarding/components/OnboardingMosaic';
import { PersonalizedOnboardingScene } from '../features/onboarding/components/PersonalizedOnboardingScene';
import { PlanningOnboardingScene } from '../features/onboarding/components/PlanningOnboardingScene';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { colors } from '../theme/colors';

const slides = [
  { key: 'discover' },
  { key: 'plan' },
  { key: 'personalized' },
] as const;

const onboardingStepCount = slides.length;
const lastSlideIndex = slides.length - 1;

const designFrame = {
  height: 956,
  width: 440,
} as const;

const slideTransition = {
  duration: 220,
} as const;

type SlideCopyProps = {
  bottom: number;
  fontSize: number;
  title: string;
};

type TransitionAction = 'back' | 'primary';

type PrimaryActionButtonProps = {
  accessibilityHint: string;
  accessibilityLabel: string;
  busy: boolean;
  disabled?: boolean;
  label: string;
  onPress: () => void;
  reducedMotionEnabled: boolean;
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

function PrimaryActionButton({
  accessibilityHint,
  accessibilityLabel,
  busy,
  disabled = false,
  label,
  onPress,
  reducedMotionEnabled,
}: PrimaryActionButtonProps) {
  const interactionDisabled = disabled || busy;

  return (
    <Pressable
      accessibilityHint={accessibilityHint}
      accessibilityLabel={accessibilityLabel}
      accessibilityRole="button"
      accessibilityState={{ busy, disabled }}
      disabled={interactionDisabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.nextButton,
        pressed && !reducedMotionEnabled && styles.nextButtonPressed,
      ]}
    >
      {({ pressed }) => (
        <>
          <LinearGradient
            colors={
              disabled
                ? [colors.disabledButton, colors.disabledButton]
                : pressed
                  ? [colors.audioTeal, colors.deepOcean]
                  : [colors.ink, colors.ink]
            }
            end={{ x: 1, y: 0.5 }}
            pointerEvents="none"
            start={{ x: 0, y: 0.5 }}
            style={styles.nextButtonSurface}
          />
          <Text style={styles.nextText}>{label}</Text>
          <View
            accessibilityElementsHidden
            importantForAccessibility="no-hide-descendants"
            style={styles.nextIcon}
          >
            <DirectionIcon direction="next" />
          </View>
        </>
      )}
    </Pressable>
  );
}

export default function OnboardingScreen() {
  const { t } = useTranslation();
  const { height, width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const [slideIndex, setSlideIndex] = useState(0);
  const [remainingSlidesPrepared, setRemainingSlidesPrepared] = useState(false);
  const [transitionAction, setTransitionAction] = useState<TransitionAction | null>(null);
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
  const titleFontSize = 37 * designScale;
  // Figma title ends at y=762 on the 440×956 reference frame.
  const copyBottom = Math.max(buttonBottom + 150 * designScale, height - 762 * designScale);
  const isFinalStep = slideIndex === onboardingStepCount - 1;
  const primaryButtonBusy = transitionAction !== null;

  useEffect(() => {
    // Mount the remaining scenes immediately after the first frame so a fast tap
    // never has to build their images and SVG hierarchy during a transition.
    scheduledFrame.current = requestAnimationFrame(() => {
      scheduledFrame.current = null;
      setRemainingSlidesPrepared(true);
    });

    return () => {
      transitionProgress.stopAnimation();

      if (scheduledFrame.current !== null) {
        cancelAnimationFrame(scheduledFrame.current);
      }
    };
  }, [transitionProgress]);

  const changeSlide = useCallback(
    (nextIndex: number, action: TransitionAction) => {
      if (nextIndex < 0 || nextIndex > lastSlideIndex || isAnimating.current) {
        return;
      }

      isAnimating.current = true;
      setTransitionAction(action);
      const runTransition = () => {
        Animated.timing(transitionProgress, {
          duration: reducedMotionEnabled ? 0 : slideTransition.duration,
          easing: Easing.out(Easing.cubic),
          toValue: nextIndex,
          useNativeDriver,
        }).start(({ finished }) => {
          if (finished) {
            setSlideIndex(nextIndex);
          }

          isAnimating.current = false;
          setTransitionAction(null);
        });
      };

      if (nextIndex > 0 && !remainingSlidesPrepared) {
        setRemainingSlidesPrepared(true);
        scheduledFrame.current = requestAnimationFrame(() => {
          scheduledFrame.current = null;
          runTransition();
        });
        return;
      }

      runTransition();
    },
    [reducedMotionEnabled, remainingSlidesPrepared, transitionProgress, useNativeDriver],
  );

  const handleNext = useCallback(() => {
    if (slideIndex < lastSlideIndex) {
      changeSlide(slideIndex + 1, 'primary');
    }
  }, [changeSlide, slideIndex]);

  const handlePrimaryPress = useCallback(() => {
    if (isFinalStep) {
      router.replace('/welcome');
      return;
    }

    handleNext();
  }, [handleNext, isFinalStep]);

  const handleBack = useCallback(() => {
    if (slideIndex > 0) {
      changeSlide(slideIndex - 1, 'back');
    }
  }, [changeSlide, slideIndex]);

  const handleSkip = useCallback(() => {
    router.replace('/welcome');
  }, []);

  return (
    <View style={styles.screen}>
      <StatusBar style="dark" />

      <Animated.View
        accessibilityElementsHidden={slideIndex !== 0}
        aria-hidden={slideIndex !== 0}
        importantForAccessibility={slideIndex === 0 ? 'auto' : 'no-hide-descendants'}
        pointerEvents="none"
        renderToHardwareTextureAndroid
        shouldRasterizeIOS
        style={[
          styles.slideLayer,
          {
            opacity: transitionProgress.interpolate({
              extrapolate: 'clamp',
              inputRange: [0, 1],
              outputRange: [1, 0],
            }),
          },
        ]}
      >
        <OnboardingMosaic height={height} width={width} />
        <SlideCopy bottom={copyBottom} fontSize={titleFontSize} title={t('onboarding.slides.discover')} />
      </Animated.View>

      {remainingSlidesPrepared ? (
        <>
          <Animated.View
            accessibilityElementsHidden={slideIndex !== 1}
        aria-hidden={slideIndex !== 1}
            importantForAccessibility={slideIndex === 1 ? 'auto' : 'no-hide-descendants'}
            pointerEvents="none"
            renderToHardwareTextureAndroid
            shouldRasterizeIOS
            style={[
              styles.slideLayer,
              {
                opacity: transitionProgress.interpolate({
                  extrapolate: 'clamp',
                  inputRange: [0, 1, 2],
                  outputRange: [0, 1, 0],
                }),
              },
            ]}
          >
            <PlanningOnboardingScene height={height} width={width} />
            <SlideCopy bottom={copyBottom} fontSize={titleFontSize} title={t('onboarding.slides.plan')} />
          </Animated.View>

          <Animated.View
            accessibilityElementsHidden={slideIndex !== 2}
        aria-hidden={slideIndex !== 2}
            importantForAccessibility={slideIndex === 2 ? 'auto' : 'no-hide-descendants'}
            pointerEvents="none"
            renderToHardwareTextureAndroid
            shouldRasterizeIOS
            style={[
              styles.slideLayer,
              {
                opacity: transitionProgress.interpolate({
                  extrapolate: 'clamp',
                  inputRange: [1, 2],
                  outputRange: [0, 1],
                }),
              },
            ]}
          >
            <PersonalizedOnboardingScene height={height} width={width} />
            <SlideCopy bottom={copyBottom} fontSize={titleFontSize} title={t('onboarding.slides.personalized')} />
          </Animated.View>
        </>
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
          accessibilityHint={t('onboarding.skipHint')}
          accessibilityLabel={t('onboarding.skipLabel')}
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
            pressed && styles.skipButtonPressed,
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
            {t('onboarding.skip')}
          </Text>
        </Pressable>
      </View>

      <View style={[styles.pagination, { bottom: buttonBottom + 90 }]}>
        {Array.from({ length: onboardingStepCount }, (_, index) => (
          <View
            accessibilityLabel={t('onboarding.page', { current: index + 1, total: onboardingStepCount })}
            key={`onboarding-page-${index + 1}`}
            style={[styles.pageDot, index === slideIndex && styles.pageDotActive]}
          />
        ))}
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
            accessibilityHint={t('onboarding.backHint')}
            accessibilityLabel={t('onboarding.backLabel')}
            accessibilityRole="button"
            accessibilityState={{ disabled: transitionAction !== null }}
            disabled={transitionAction !== null}
            onPress={handleBack}
            style={({ pressed }) => [styles.backButton, pressed && styles.backButtonPressed]}
          >
            <DirectionIcon direction="back" />
          </Pressable>
        ) : null}

        <PrimaryActionButton
          accessibilityHint={t(isFinalStep ? 'onboarding.startHint' : 'onboarding.nextHint')}
          accessibilityLabel={t(isFinalStep ? 'onboarding.startLabel' : 'onboarding.nextLabel')}
          busy={primaryButtonBusy}
          label={t(isFinalStep ? 'onboarding.start' : 'onboarding.next')}
          onPress={handlePrimaryPress}
          reducedMotionEnabled={reducedMotionEnabled}
        />
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
    shadowColor: colors.ink,
    shadowOffset: { height: 4, width: 0 },
    shadowOpacity: 0.1,
    shadowRadius: 20,
  },
  skipText: {
    color: colors.deepOcean,
    fontFamily: 'HankenGrotesk_700Bold',
  },
  skipButtonPressed: {
    backgroundColor: 'rgba(255,255,255,0.32)',
    transform: [{ scale: 0.98 }],
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
    fontFamily: 'HankenGrotesk_500Medium',
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
    elevation: 5,
    shadowColor: colors.audioTeal,
    shadowOffset: { height: 3, width: 0 },
    shadowOpacity: 0.22,
    shadowRadius: 10,
    transform: [{ scale: 0.985 }],
  },
  nextButtonSurface: {
    borderRadius: 30,
    bottom: 0,
    left: 0,
    position: 'absolute',
    right: 0,
    top: 0,
  },
  nextText: {
    color: colors.white,
    fontSize: 20,
    fontFamily: 'HankenGrotesk_700Bold',
    lineHeight: 24,
  },
  nextIcon: {
    marginLeft: 6,
    transform: [{ scale: 0.58 }],
  },
});

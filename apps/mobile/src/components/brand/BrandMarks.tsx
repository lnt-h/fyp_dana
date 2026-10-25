import { useEffect, useRef } from 'react';
import { Animated, Platform, StyleSheet, View } from 'react-native';
import Svg, {
  Circle,
  Defs,
  LinearGradient as SvgLinearGradient,
  Path,
  Stop,
} from 'react-native-svg';

import { colors } from '../../theme/colors';
import { useReducedMotion } from '../../hooks/useReducedMotion';

const loadingAnimation = {
  dotCount: 3,
  dotSize: 4,
  gap: 4,
  pauseDuration: 240,
  pulseDuration: 180,
  staggerDelay: 120,
} as const;

export function SplashLogo() {
  return (
    <Svg accessibilityRole="image" height={99} viewBox="0 0 78.6462 98.8539" width={79}>
      <Path
        d="M56.8 37.6846C56.8 49.7499 47.0192 59.5308 34.9539 59.5308C22.8886 59.5308 13.1077 49.7499 13.1077 37.6846C13.1077 25.6193 22.8886 15.8385 34.9539 15.8385C47.0192 15.8385 56.8 25.6193 56.8 37.6846Z"
        fill="none"
        stroke={colors.white}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={15.2923}
      />
      <Path
        d="M55.7077 24.5769V64.4462C55.7077 80.2846 46.4231 91.2077 32.2231 91.2077C21.8462 91.2077 14.2 87.9308 7.6462 81.9231"
        fill="none"
        stroke={colors.white}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={15.2923}
      />
      <Circle cx={71.5461} cy={7.1} fill={colors.sun} r={7.1} />
    </Svg>
  );
}

export function LoadingDots() {
  const progress = useRef(
    Array.from({ length: loadingAnimation.dotCount }, () => new Animated.Value(0)),
  ).current;
  const reduceMotionEnabled = useReducedMotion();
  const useNativeDriver = Platform.OS !== 'web';

  useEffect(() => {
    progress.forEach((value) => {
      value.stopAnimation();
      value.setValue(reduceMotionEnabled ? 0.5 : 0);
    });

    if (reduceMotionEnabled) {
      return;
    }

    const pulses = progress.map((value) =>
      Animated.sequence([
        Animated.timing(value, {
          duration: loadingAnimation.pulseDuration,
          toValue: 1,
          useNativeDriver,
        }),
        Animated.timing(value, {
          duration: loadingAnimation.pulseDuration,
          toValue: 0,
          useNativeDriver,
        }),
      ]),
    );

    const animation = Animated.loop(
      Animated.sequence([
        Animated.stagger(loadingAnimation.staggerDelay, pulses),
        Animated.delay(loadingAnimation.pauseDuration),
      ]),
    );

    animation.start();
    return () => animation.stop();
  }, [progress, reduceMotionEnabled, useNativeDriver]);

  return (
    <View
      accessibilityLabel="Loading Gonarra"
      accessibilityRole="progressbar"
      style={styles.loadingDots}
    >
      {progress.map((value, index) => (
        <Animated.View
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
          key={`loading-dot-${index}`}
          style={[
            styles.loadingDot,
            {
              opacity: value.interpolate({
                inputRange: [0, 1],
                outputRange: [0.35, 1],
              }),
              transform: [
                {
                  scale: value.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0.8, 1.2],
                  }),
                },
              ],
            },
          ]}
        />
      ))}
    </View>
  );
}

const wordmarkPaths = [
  'M19.7834 12.1362C19.7834 15.7171 16.8805 18.62 13.2997 18.62C9.71879 18.62 6.81592 15.7171 6.81592 12.1362C6.81592 8.55537 9.71879 5.6525 13.2997 5.6525C16.8805 5.6525 19.7834 8.55537 19.7834 12.1362Z',
  'M19.6173 8.14625V20.2825C19.6173 25.1037 16.7911 28.4287 12.4686 28.4287C9.3098 28.4287 6.9823 27.4312 4.9873 25.6025',
  'M41.5622 13.6325C41.5622 17.1216 38.7338 19.95 35.2447 19.95C31.7557 19.95 28.9272 17.1216 28.9272 13.6325C28.9272 10.1434 31.7557 7.315 35.2447 7.315C38.7338 7.315 41.5622 10.1434 41.5622 13.6325Z',
  'M48.3789 21.28V13.965M48.3789 13.965V8.97749M48.3789 13.965C48.3789 10.1412 51.0389 8.14624 54.6964 8.14624C57.8552 8.14624 59.6839 10.4737 59.6839 14.1312V21.28',
];

const gradientWordmarkPaths = [
  'M78.9685 13.965C78.9685 17.4541 76.1401 20.2825 72.651 20.2825C69.1619 20.2825 66.3335 17.4541 66.3335 13.965C66.3335 10.4759 69.1619 7.64751 72.651 7.64751C76.1401 7.64751 78.9685 10.4759 78.9685 13.965Z',
  'M78.9683 8.47876V21.28',
  'M85.7847 21.28V13.7988M85.7847 13.7988V8.97751M85.7847 13.7988C85.7847 10.1413 88.4447 8.14626 91.4372 8.14626C92.7672 8.14626 93.7647 8.47876 94.4297 8.97751',
  'M101.246 21.28V13.7988M101.246 13.7988V8.97751M101.246 13.7988C101.246 10.1413 103.906 8.14626 106.899 8.14626C108.229 8.14626 109.226 8.47876 109.891 8.97751',
  'M129.01 13.965C129.01 17.4541 126.182 20.2825 122.692 20.2825C119.203 20.2825 116.375 17.4541 116.375 13.965C116.375 10.4759 119.203 7.6475 122.692 7.6475C126.182 7.6475 129.01 10.4759 129.01 13.965Z',
  'M129.01 8.47876V21.28',
];

const wordmarkAspectRatio = 133 / 32;

type WordmarkProps = {
  width: number;
};

export function Wordmark({ width }: WordmarkProps) {
  const height = width / wordmarkAspectRatio;

  return (
    <View accessibilityLabel="Gonarra" accessibilityRole="image" style={{ height, width }}>
      <Svg height="100%" viewBox="0 0 133 32" width="100%">
        <Defs>
          <SvgLinearGradient id="wordmark" x1="64" x2="131" y1="0" y2="0">
            <Stop offset="0" stopColor={colors.deepOcean} />
            <Stop offset="1" stopColor={colors.tealDark} />
          </SvgLinearGradient>
        </Defs>
        {wordmarkPaths.map((path) => (
          <Path
            d={path}
            fill="none"
            key={path}
            stroke={colors.deepOcean}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={4.3225}
          />
        ))}
        <Circle cx={24.4387} cy={2.82625} fill={colors.sun} r={1.91188} />
        {gradientWordmarkPaths.map((path) => (
          <Path
            d={path}
            fill="none"
            key={path}
            stroke="url(#wordmark)"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={4.3225}
          />
        ))}
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  loadingDot: {
    backgroundColor: colors.white,
    borderRadius: loadingAnimation.dotSize / 2,
    height: loadingAnimation.dotSize,
    width: loadingAnimation.dotSize,
  },
  loadingDots: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: loadingAnimation.gap,
    justifyContent: 'center',
  },
});

import { memo } from 'react';
import { Image, ImageSourcePropType, StyleSheet, View } from 'react-native';

import {
  OnboardingLowerFade,
  OnboardingPatternBackdrop,
} from './OnboardingPatternBackground';

const planningHero = require('../../../../assets/images/onboarding/planning-hero.png') as ImageSourcePropType;
const designFrame = {
  height: 956,
  width: 440,
} as const;

const exportedHero = {
  height: 400,
  left: 11,
  top: 160,
  width: 419,
} as const;

type Props = {
  height: number;
  width: number;
};

export const PlanningOnboardingScene = memo(function PlanningOnboardingScene({ height, width }: Props) {
  const scale = Math.min(width / designFrame.width, height / designFrame.height);
  const canvasWidth = designFrame.width * scale;
  const canvasHeight = designFrame.height * scale;
  const canvasLeft = (width - canvasWidth) / 2;

  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <OnboardingPatternBackdrop height={height} variant="planning" width={width} />
      <OnboardingLowerFade height={height} variant="planning" width={width} />
      <Image
        accessibilityIgnoresInvertColors
        resizeMode="contain"
        source={planningHero}
        style={[
          styles.preview,
          {
            height: exportedHero.height * scale,
            left: canvasLeft + exportedHero.left * scale,
            top: exportedHero.top * scale,
            width: exportedHero.width * scale,
          },
        ]}
      />
    </View>
  );
});

const styles = StyleSheet.create({
  preview: {
    position: 'absolute',
  },
});

import { memo } from 'react';
import { StyleSheet, View } from 'react-native';

import {
  OnboardingLowerFade,
  OnboardingPatternBackdrop,
} from './OnboardingPatternBackground';

type Props = {
  height: number;
  width: number;
};

/**
 * The current Figma export intentionally has no foreground illustration on
 * this step. Its visual depth comes from the glass pattern and the two fade
 * layers; the legacy grey placeholder is not part of the shipped design.
 */
export const PersonalizedOnboardingScene = memo(function PersonalizedOnboardingScene({
  height,
  width,
}: Props) {
  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <OnboardingPatternBackdrop height={height} variant="personalized" width={width} />
      <OnboardingLowerFade height={height} variant="personalized" width={width} />
    </View>
  );
});

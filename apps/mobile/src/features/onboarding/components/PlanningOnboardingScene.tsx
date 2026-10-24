import { LinearGradient } from 'expo-linear-gradient';
import { Image, ImageSourcePropType, StyleSheet, View } from 'react-native';

const planningPreview = require('../../../../assets/onboarding/plan-tour.png') as ImageSourcePropType;
const patternCells = Array.from({ length: 100 }, (_, index) => index);

const designFrame = {
  height: 956,
  width: 440,
} as const;

const designPreview = {
  height: 336.5521,
  top: 192.6003,
  width: 355.5391,
} as const;

const designPattern = {
  cell: 90.2076,
  cornerRadius: 16.0611,
  left: -290.5,
  step: 96.0322,
  top: 31,
} as const;

type Props = {
  height: number;
  width: number;
};

export function PlanningOnboardingScene({ height, width }: Props) {
  const scale = Math.min(width / designFrame.width, height / designFrame.height);
  const previewWidth = designPreview.width * scale;
  const previewHeight = designPreview.height * scale;
  const previewTop = designPreview.top * scale;
  const patternCell = designPattern.cell * scale;
  const patternStep = designPattern.step * scale;
  const fadeTop = 463 * scale;

  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <LinearGradient
        colors={['#BBE9FF', 'rgba(255,255,255,0)']}
        locations={[0, 1]}
        style={StyleSheet.absoluteFill}
      />

      <View
        style={[
          styles.pattern,
          {
            height: designPattern.step * 10 * scale,
            left: designPattern.left * scale,
            top: designPattern.top * scale,
            width: designPattern.step * 10 * scale,
          },
        ]}
      >
        {patternCells.map((cell) => (
          <View
            key={cell}
            style={[
              styles.patternCell,
              {
                borderRadius: designPattern.cornerRadius * scale,
                height: patternCell,
                left: (cell % 10) * patternStep,
                top: Math.floor(cell / 10) * patternStep,
                width: patternCell,
              },
            ]}
          />
        ))}
      </View>

      <LinearGradient
        colors={[
          'rgba(255,255,255,0)',
          'rgba(255,255,255,0.25)',
          'rgba(255,255,255,0.5)',
          '#FFFFFF',
          '#FFFFFF',
        ]}
        locations={[0, 0.12545185, 0.27795538, 0.5940541, 1]}
        style={[styles.fade, { height: Math.max(0, height - fadeTop), top: fadeTop }]}
      />

      <Image
        accessibilityIgnoresInvertColors
        resizeMode="contain"
        source={planningPreview}
        style={[
          styles.preview,
          {
            height: previewHeight,
            left: (width - previewWidth) / 2,
            top: previewTop,
            width: previewWidth,
          },
        ]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  pattern: {
    position: 'absolute',
  },
  patternCell: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    position: 'absolute',
  },
  fade: {
    left: 0,
    position: 'absolute',
    right: 0,
  },
  preview: {
    position: 'absolute',
  },
});

import { LinearGradient } from 'expo-linear-gradient';
import { Image, ImageSourcePropType, StyleSheet, View } from 'react-native';

const planningPreview = require('../../../../assets/onboarding/plan-tour.png') as ImageSourcePropType;
const patternCells = Array.from({ length: 60 }, (_, index) => index);

type Props = {
  height: number;
  width: number;
};

export function PlanningOnboardingScene({ height, width }: Props) {
  const previewWidth = Math.min(width * 0.81, 380);
  const previewHeight = previewWidth * (673 / 711);
  const previewTop = Math.max(height * 0.19, 142);

  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <LinearGradient
        colors={['#D7F4FA', '#EAF8FC', '#FFFFFF']}
        locations={[0, 0.5, 0.9]}
        style={StyleSheet.absoluteFill}
      />

      <View style={styles.pattern}>
        {patternCells.map((cell) => (
          <View key={cell} style={styles.patternCell} />
        ))}
      </View>

      <LinearGradient
        colors={['rgba(255,255,255,0)', 'rgba(255,255,255,0.42)', '#FFFFFF']}
        locations={[0, 0.34, 0.72]}
        style={[styles.fade, { height: height * 0.58, top: height * 0.42 }]}
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
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 7,
    left: -44,
    opacity: 0.3,
    position: 'absolute',
    right: -44,
    top: 178,
  },
  patternCell: {
    aspectRatio: 1,
    backgroundColor: 'rgba(255,255,255,0.42)',
    borderRadius: 16,
    width: '19%',
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

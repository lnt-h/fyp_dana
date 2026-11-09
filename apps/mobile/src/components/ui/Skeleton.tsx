import { LinearGradient } from 'expo-linear-gradient';
import { useEffect, useRef, useState } from 'react';
import { Animated, Easing, StyleSheet, View, type DimensionValue, type StyleProp, type ViewStyle } from 'react-native';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { colors } from '../../theme/colors';

export type SkeletonProps = {
  width?: DimensionValue;
  height?: DimensionValue;
  /** Default 12; use radii.card (16) for card placeholders, height/2 for circles. */
  radius?: number;
  style?: StyleProp<ViewStyle>;
};

/** Loading placeholder with a sweeping shimmer; static when reduced motion is on. Hidden from screen readers. */
export function Skeleton({ width = '100%', height = 16, radius = 12, style }: SkeletonProps) {
  const reduced = useReducedMotion();
  const progress = useRef(new Animated.Value(0)).current;
  const [boxWidth, setBoxWidth] = useState(0);

  useEffect(() => {
    if (reduced || boxWidth === 0) return;
    const loop = Animated.loop(
      Animated.timing(progress, { duration: 1300, easing: Easing.inOut(Easing.ease), toValue: 1, useNativeDriver: true }),
    );
    loop.start();
    return () => {
      loop.stop();
      progress.setValue(0);
    };
  }, [boxWidth, progress, reduced]);

  const translateX = progress.interpolate({ inputRange: [0, 1], outputRange: [-boxWidth, boxWidth] });

  return (
    <View
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      onLayout={event => setBoxWidth(event.nativeEvent.layout.width)}
      style={[styles.base, { borderRadius: radius, height, width }, style]}
    >
      {!reduced && boxWidth > 0 ? (
        <Animated.View style={[StyleSheet.absoluteFill, { transform: [{ translateX }] }]}>
          <LinearGradient
            colors={['rgba(255,255,255,0)', 'rgba(255,255,255,0.7)', 'rgba(255,255,255,0)']}
            end={{ x: 1, y: 0.5 }}
            start={{ x: 0, y: 0.5 }}
            style={StyleSheet.absoluteFill}
          />
        </Animated.View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  base: { backgroundColor: colors.surface, overflow: 'hidden' },
});

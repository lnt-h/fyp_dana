import { useEffect, useRef } from 'react';
import { Animated, Easing, StyleSheet, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { useReducedMotion } from '../../hooks/useReducedMotion';
import { colors } from '../../theme/colors';

const SIZE = 88;

/**
 * Decorative ✓ (SCR-029 success): a teal disc that settles in, then a white check fades up. Total ≤ 220 ms per step,
 * no confetti; static under reduced motion. Hidden from screen readers (the title carries the meaning).
 */
export function SuccessCheck() {
  const reduced = useReducedMotion();
  const disc = useRef(new Animated.Value(reduced ? 1 : 0)).current;
  const mark = useRef(new Animated.Value(reduced ? 1 : 0)).current;

  useEffect(() => {
    if (reduced) {
      disc.setValue(1);
      mark.setValue(1);
      return;
    }
    const sequence = Animated.sequence([
      Animated.timing(disc, { duration: 220, easing: Easing.out(Easing.back(1.6)), toValue: 1, useNativeDriver: true }),
      Animated.timing(mark, { duration: 180, easing: Easing.out(Easing.cubic), toValue: 1, useNativeDriver: true }),
    ]);
    sequence.start();
    return () => sequence.stop();
  }, [disc, mark, reduced]);

  const scale = disc.interpolate({ inputRange: [0, 1], outputRange: [0.6, 1] });
  const markShift = mark.interpolate({ inputRange: [0, 1], outputRange: [6, 0] });

  return (
    <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.wrap}>
      <View style={styles.halo} />
      <Animated.View style={[styles.disc, { opacity: disc, transform: [{ scale }] }]}>
        <Animated.View style={{ opacity: mark, transform: [{ translateY: markShift }] }}>
          <Svg fill="none" height={44} viewBox="0 0 24 24" width={44}>
            <Path d="M5 12.5l4.5 4.5L19 7.5" stroke={colors.white} strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.6} />
          </Svg>
        </Animated.View>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  disc: { alignItems: 'center', backgroundColor: colors.audioTeal, borderRadius: SIZE / 2, height: SIZE, justifyContent: 'center', width: SIZE },
  halo: { backgroundColor: colors.surfaceTint, borderRadius: (SIZE + 32) / 2, height: SIZE + 32, position: 'absolute', width: SIZE + 32 },
  wrap: { alignItems: 'center', alignSelf: 'center', height: SIZE + 32, justifyContent: 'center', width: SIZE + 32 },
});

import { StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors, dayPinColor } from '../../theme/colors';
import { fonts } from '../../theme/typography';

export type NumberPinProps = {
  /** Number shown in the pin (stop order, 1-based). */
  number: number;
  /** 0-based day index: picks the day colour (teal, coral, indigo). */
  dayIndex?: number;
  /** Diameter: 24 (timeline rows) or 28 (map, focus). Default 28. */
  size?: 24 | 28;
  /** Spoken label, e.g. "Stop 2, day 1". Omit when the row already announces the order (pin is then hidden). */
  accessibilityLabel?: string;
  style?: StyleProp<ViewStyle>;
};

/**
 * Numbered circular pin in the day colour with a white bold number (≥ 4.5:1: day 2 uses coralText, see `dayPinColors`).
 * The same component marks timeline stops and map pins so the two read as one revision.
 */
export function NumberPin({ number, dayIndex = 0, size = 28, accessibilityLabel, style }: NumberPinProps) {
  return (
    <View
      accessibilityElementsHidden={!accessibilityLabel}
      accessibilityLabel={accessibilityLabel}
      accessible={!!accessibilityLabel}
      importantForAccessibility={accessibilityLabel ? 'yes' : 'no-hide-descendants'}
      style={[styles.pin, { backgroundColor: dayPinColor(dayIndex), borderRadius: size / 2, height: size, width: size }, style]}
    >
      <Text allowFontScaling={false} style={[styles.text, { fontSize: size === 24 ? 12 : 14 }]}>{number}</Text>
    </View>
  );
}

export type DayDotProps = {
  /** 0-based day index. */
  dayIndex: number;
  /** Dot diameter (default 10). */
  size?: number;
  style?: StyleProp<ViewStyle>;
};

/** Small decorative dot in the day colour (day chips, legends). */
export function DayDot({ dayIndex, size = 10, style }: DayDotProps) {
  return (
    <View
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={[{ backgroundColor: dayPinColor(dayIndex), borderRadius: size / 2, height: size, width: size }, style]}
    />
  );
}

const styles = StyleSheet.create({
  pin: { alignItems: 'center', borderColor: colors.white, borderWidth: 2, justifyContent: 'center' },
  text: { color: colors.white, fontFamily: fonts.bold, includeFontPadding: false, textAlign: 'center' },
});

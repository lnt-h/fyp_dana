import { StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors } from '../../theme/colors';
import { typography } from '../../theme/typography';
import { Icon, type IconName } from './Icon';

export type StatCircleProps = {
  icon: IconName;
  value: string;
  label: string;
  /** Circle diameter (default 64). */
  size?: number;
  style?: StyleProp<ViewStyle>;
};

/** Icon in a primarySoft circle, value below, muted label. Read as one element ("3 ngày, Thời lượng"). */
export function StatCircle({ icon, value, label, size = 64, style }: StatCircleProps) {
  return (
    <View accessible accessibilityLabel={`${value}, ${label}`} style={[styles.root, style]}>
      <View style={[styles.circle, { borderRadius: size / 2, height: size, width: size }]}>
        <Icon color={colors.primary} name={icon} size={Math.round(size * 0.42)} />
      </View>
      <Text numberOfLines={1} style={styles.value}>{value}</Text>
      <Text numberOfLines={2} style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  circle: { alignItems: 'center', backgroundColor: colors.primarySoft, justifyContent: 'center', marginBottom: 10 },
  label: { ...typography.caption, fontSize: 14, textAlign: 'center' },
  root: { alignItems: 'center', flex: 1, minWidth: 0 },
  value: { ...typography.headline, textAlign: 'center' },
});

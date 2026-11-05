import { StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors } from '../../theme/colors';
import { fonts } from '../../theme/typography';
import { Icon, type IconName } from './Icon';

export type GlassBadgeProps = {
  label: string;
  icon?: IconName;
  style?: StyleProp<ViewStyle>;
};

/**
 * Translucent dark pill for use over photos (e.g. "2 ngày"). The ink 55% fill keeps white text ≥4.5:1 on any photo.
 * No native blur dependency; reads as glass via the hairline border.
 */
export function GlassBadge({ label, icon, style }: GlassBadgeProps) {
  return (
    <View accessible accessibilityLabel={label} style={[styles.badge, style]}>
      {icon ? <Icon color={colors.white} name={icon} size={15} /> : null}
      <Text numberOfLines={1} style={styles.text}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(7,21,30,0.55)',
    borderColor: 'rgba(255,255,255,0.28)',
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    flexDirection: 'row',
    gap: 6,
    minHeight: 30,
    paddingHorizontal: 12,
    paddingVertical: 5,
  },
  text: { color: colors.white, fontFamily: fonts.bold, fontSize: 13, lineHeight: 18 },
});

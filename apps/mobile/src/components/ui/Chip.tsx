import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors } from '../../theme/colors';
import { radii } from '../../theme/spacing';
import { fonts } from '../../theme/typography';
import { Icon, type IconName } from './Icon';

const border = '#DCE8EE';

export type ChipProps = {
  label: string;
  icon?: IconName;
  /** Selected chips fill with deepOcean (white text). */
  selected?: boolean;
  /** Pressable when set (toggle semantics if `selected` is defined). */
  onPress?: () => void;
  disabled?: boolean;
  /** `default` = outline on white; `tint` = skyWash fill, tealText label. */
  tone?: 'default' | 'tint';
  accessibilityLabel?: string;
  style?: StyleProp<ViewStyle>;
};

export function Chip({ label, icon, selected, onPress, disabled, tone = 'default', accessibilityLabel, style }: ChipProps) {
  const fg = selected ? colors.white : tone === 'tint' ? colors.tealText : colors.ink;
  const body = (
    <>
      {icon ? <Icon color={fg} name={icon} size={16} /> : null}
      <Text numberOfLines={1} style={[styles.text, { color: fg }]}>{label}</Text>
    </>
  );
  const look = [styles.chip, tone === 'tint' && styles.tint, selected && styles.selected, disabled && styles.disabled, style];
  if (!onPress) {
    return <View accessible accessibilityLabel={accessibilityLabel ?? label} style={look}>{body}</View>;
  }
  return (
    <Pressable
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityRole={selected === undefined ? 'button' : 'checkbox'}
      accessibilityState={{ checked: selected, disabled: !!disabled }}
      disabled={disabled}
      hitSlop={{ bottom: 4, top: 4 }}
      onPress={onPress}
      style={({ pressed }) => [look, pressed && styles.pressed]}
    >
      {body}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: colors.white,
    borderColor: border,
    borderRadius: radii.chip,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 6,
    minHeight: 40,
    paddingHorizontal: 14,
  },
  disabled: { opacity: 0.45 },
  pressed: { opacity: 0.8 },
  selected: { backgroundColor: colors.deepOcean, borderColor: colors.deepOcean },
  text: { fontFamily: fonts.bold, fontSize: 14, lineHeight: 19 },
  tint: { backgroundColor: colors.skyWash, borderColor: colors.skyWash },
});

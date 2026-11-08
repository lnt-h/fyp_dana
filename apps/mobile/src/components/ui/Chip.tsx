import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors, type CategoryTone } from '../../theme/colors';
import { radii } from '../../theme/spacing';
import { fonts } from '../../theme/typography';
import { Icon, type IconName } from './Icon';

export type ChipProps = {
  label: string;
  /** Optional leading icon. */
  icon?: IconName;
  /** Selected chips fill with primarySoft and use primary text (4.59:1). */
  selected?: boolean;
  /** Pressable when set (toggle semantics if `selected` is defined). */
  onPress?: () => void;
  disabled?: boolean;
  /**
   * `default` = white with a hairline outline; `tint` = surface fill; a `CategoryTone` (from `categoryColor(code)`)
   * = category soft fill with the icon in the category colour. Labels stay ink (category colours are icon-only).
   */
  tone?: 'default' | 'tint' | CategoryTone;
  accessibilityLabel?: string;
  style?: StyleProp<ViewStyle>;
};

/** Pill chip, 40 tall: filters, choices and category labels. */
export function Chip({ label, icon, selected, onPress, disabled, tone = 'default', accessibilityLabel, style }: ChipProps) {
  const category = typeof tone === 'object' ? tone : null;
  const fg = selected ? colors.primary : colors.ink;
  const iconColor = selected ? colors.primary : category ? category.fg : colors.textSecondary;
  const body = (
    <>
      {icon ? <Icon color={iconColor} name={icon} size={16} strokeWidth={2} /> : null}
      <Text maxFontSizeMultiplier={1.4} numberOfLines={1} style={[styles.text, { color: fg }]}>{label}</Text>
    </>
  );
  const look = [
    styles.chip,
    tone === 'tint' && styles.tint,
    category && { backgroundColor: category.bg, borderColor: category.bg },
    selected && styles.selected,
    disabled && styles.disabled,
    style,
  ];
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
    borderColor: colors.hairline,
    borderRadius: radii.pill,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 6,
    minHeight: 40,
    paddingHorizontal: 14,
  },
  disabled: { opacity: 0.45 },
  pressed: { opacity: 0.8 },
  selected: { backgroundColor: colors.primarySoft, borderColor: colors.primarySoft },
  text: { fontFamily: fonts.semibold, fontSize: 14, lineHeight: 19 },
  tint: { backgroundColor: colors.surface, borderColor: colors.surface },
});

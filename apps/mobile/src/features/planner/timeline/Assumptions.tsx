import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Icon } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

/**
 * The preview's `assumptions` (server-localized lines) as ONE collapsed "Assumptions" row; tapping shows the lines as
 * written. Nothing here rewrites or filters them.
 */
export function Assumptions({ lines, style }: { lines: string[]; style?: object }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const items = lines.map(line => line.trim()).filter(Boolean);
  if (!items.length) return null;
  return <View style={style}>
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ expanded: open }}
      onPress={() => setOpen(value => !value)}
      style={({ pressed }) => [a.row, pressed && a.pressed]}
    >
      <Icon color={colors.textSecondary} name="info" size={16} />
      <Text style={a.title}>{t('proposal.assumptions.title', { count: items.length })}</Text>
      <Icon color={colors.textMuted} name={open ? 'chevron-up' : 'chevron-down'} size={16} strokeWidth={2} />
    </Pressable>
    {open ? <View style={a.list}>
      {items.map((line, index) => <Text key={`${index}-${line}`} style={a.text}>{line}</Text>)}
    </View> : null}
  </View>;
}

const a = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, minHeight: MIN_TOUCH },
  pressed: { opacity: 0.6 },
  title: { flex: 1, fontFamily: fonts.medium, fontSize: 14, lineHeight: 20, color: colors.textSecondary },
  list: { gap: spacing.xxs, paddingLeft: spacing.xl, paddingBottom: spacing.xs },
  text: { fontFamily: fonts.regular, fontSize: 13, lineHeight: 19, color: colors.textMuted },
});

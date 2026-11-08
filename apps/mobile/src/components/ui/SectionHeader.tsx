import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors } from '../../theme/colors';
import { MIN_TOUCH } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { Icon } from './Icon';

export type SectionHeaderProps = {
  title: string;
  subtitle?: string;
  /** Link label, e.g. t('common.seeAll') → "See all" / "Xem tất cả". Shown only with `onAction`. */
  actionLabel?: string;
  onAction?: () => void;
  style?: StyleProp<ViewStyle>;
};

export function SectionHeader({ title, subtitle, actionLabel, onAction, style }: SectionHeaderProps) {
  return (
    <View style={[styles.row, style]}>
      <View style={styles.titles}>
        <Text accessibilityRole="header" style={styles.title}>{title}</Text>
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      </View>
      {actionLabel && onAction ? (
        <Pressable accessibilityRole="link" hitSlop={8} onPress={onAction} style={({ pressed }) => [styles.action, pressed && { opacity: 0.7 }]}>
          <Text style={styles.actionText}>{actionLabel}</Text>
          <Icon color={colors.primary} name="chevron-right" size={18} />
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  action: { alignItems: 'center', flexDirection: 'row', gap: 2, minHeight: MIN_TOUCH, paddingLeft: 12 },
  actionText: { color: colors.primary, fontFamily: fonts.semibold, fontSize: 15 },
  row: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  subtitle: { ...typography.body, color: colors.textSecondary, fontSize: 15, marginTop: 2 },
  /** Sentence case, 19 semibold. */
  title: typography.headline,
  titles: { flex: 1 },
});

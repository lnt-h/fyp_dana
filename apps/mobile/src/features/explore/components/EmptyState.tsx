import { StyleSheet, Text, View } from 'react-native';

import { Icon, SecondaryButton, type IconName } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

type Action = { label: string; onPress: () => void };

/** Calm skyWash card: glyph, title, body and up to two actions (search empty, category empty, city coming soon). */
export function EmptyState({ icon, title, body, actions = [] }: { icon: IconName; title: string; body: string; actions?: Action[] }) {
  return (
    <View style={styles.card}>
      <View style={styles.glyph}>
        <Icon color={colors.tealText} name={icon} size={28} />
        <View style={styles.sun} />
      </View>
      <Text accessibilityLiveRegion="polite" accessibilityRole="header" style={styles.title}>{title}</Text>
      <Text style={styles.body}>{body}</Text>
      {actions.length > 0 ? (
        <View style={styles.actions}>
          {actions.map(action => <SecondaryButton key={action.label} label={action.label} onPress={action.onPress} />)}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  actions: { alignSelf: 'stretch', gap: spacing.xs, marginTop: spacing.xs },
  body: { color: colors.textMuted, fontFamily: fonts.regular, fontSize: 15, lineHeight: 22, textAlign: 'center' },
  card: { alignItems: 'center', backgroundColor: colors.surfaceTint, borderRadius: radii.card, gap: 10, paddingHorizontal: spacing.lg, paddingVertical: spacing.xl },
  glyph: { alignItems: 'center', backgroundColor: colors.white, borderRadius: 32, height: 64, justifyContent: 'center', marginBottom: 4, width: 64 },
  sun: { backgroundColor: colors.sun, borderColor: colors.surfaceTint, borderRadius: 7, borderWidth: 2, height: 14, position: 'absolute', right: 2, top: 2, width: 14 },
  title: { color: colors.ink, fontFamily: fonts.bold, fontSize: 18, lineHeight: 24, textAlign: 'center' },
});

import { StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Icon } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

/**
 * The preview's `assumptions` (server-localized lines, e.g. the demo-estimate disclosure), shown as written in a
 * neutral card. Nothing here rewrites or filters them.
 */
export function Assumptions({ lines, style }: { lines: string[]; style?: object }) {
  const { t } = useTranslation();
  const items = lines.map(line => line.trim()).filter(Boolean);
  if (!items.length) return null;
  return <View style={[a.card, style]}>
    <View style={a.head}>
      <Icon color={colors.tealText} name="info" size={18} />
      <Text accessibilityRole="header" style={a.title}>{t('proposal.assumptions.title')}</Text>
    </View>
    {items.map((line, index) => <View key={`${index}-${line}`} style={a.item}>
      <View style={a.bullet} />
      <Text style={a.text}>{line}</Text>
    </View>)}
  </View>;
}

const a = StyleSheet.create({
  card: { gap: spacing.xs, padding: spacing.md, borderRadius: radii.card, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.hairline },
  head: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  title: { fontFamily: fonts.bold, fontSize: 15, lineHeight: 20, color: colors.ink },
  item: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.xs },
  bullet: { width: 5, height: 5, borderRadius: 2.5, backgroundColor: colors.textMuted, marginTop: 8 },
  text: { flex: 1, fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textMuted },
});

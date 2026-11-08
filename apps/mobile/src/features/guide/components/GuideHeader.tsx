import { useTranslation } from 'react-i18next';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';

import { CircleButton } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { typography } from '../../../theme/typography';

/** Muted text for Guide surfaces (4.74:1 on white). Kept as an alias for older imports. */
export const washMuted = colors.textMuted;

/** Gonarra avatar for the Guide: the "g" brand symbol in white on a teal disc, with the sun dot. Decorative. */
export function GuideAvatar({ size = 48 }: { size?: number }) {
  const glyph = Math.round(size * 0.56);
  return <View
    accessibilityElementsHidden
    importantForAccessibility="no-hide-descendants"
    style={[h.avatar, { borderRadius: size / 2, height: size, width: size }]}
  >
    <Svg height={glyph * 1.17} viewBox="0 0 80 94" width={glyph}>
      <Path d="M57 36a23 23 0 1 1-46 0a23 23 0 1 1 46 0M57 25v38c0 27-26 32-43 19" fill="none" stroke={colors.white} strokeLinecap="round" strokeWidth={13} />
      <Circle cx={72} cy={9} fill={colors.sun} r={8} />
    </Svg>
  </View>;
}

/** SCR-034 header: title and, in a chat, the delete-conversation button. No kicker (visual refresh 2026-11-09). */
export function GuideHeader({ onClear, clearDisabled }: { onClear?: () => void; clearDisabled?: boolean }) {
  const { t } = useTranslation();
  return <View style={h.row}>
    <View style={h.copy}>
      <Text accessibilityRole="header" numberOfLines={1} style={typography.title}>{t('guide.title')}</Text>
      <Text numberOfLines={1} style={h.subtitle}>{t('guide.subtitle')}</Text>
    </View>
    {onClear && <CircleButton accessibilityLabel={t('guide.clear')} disabled={clearDisabled} icon="trash" onPress={onClear} size={44} tone="tint" />}
  </View>;
}

const h = StyleSheet.create({
  avatar: { alignItems: 'center', backgroundColor: colors.primary, justifyContent: 'center', paddingTop: 2 },
  copy: { flex: 1, minWidth: 0 },
  row: { alignItems: 'center', flexDirection: 'row', gap: 12, paddingBottom: 12 },
  subtitle: { ...typography.caption, color: colors.textSecondary, fontSize: 14, marginTop: 2 },
});

import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { StyleSheet, Text, View } from 'react-native';

import { CircleButton, Icon } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { fonts } from '../../../theme/typography';

/** Muted text on skyWash (5.8:1); `textMuted` drops below 4.5:1 there. */
export const washMuted = '#4A6170';

/** Guide avatar: audioTeal→deepOcean circle with a sparkle. Decorative. */
export function GuideAvatar({ size = 48 }: { size?: number }) {
  return <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={[h.avatarRing, { borderRadius: size / 2 + 3, padding: 3 }]}>
    <LinearGradient colors={[colors.audioTeal, colors.deepOcean]} end={{ x: 1, y: 1 }} start={{ x: 0, y: 0 }} style={[h.avatar, { borderRadius: size / 2, height: size, width: size }]}>
      <Icon color={colors.white} name="sparkle" size={Math.round(size * 0.5)} />
    </LinearGradient>
  </View>;
}

/** SCR-034 header: avatar, "Hướng dẫn AI", subtitle and (in a chat) the clear button. */
export function GuideHeader({ onClear, clearDisabled }: { onClear?: () => void; clearDisabled?: boolean }) {
  const { t } = useTranslation();
  return <View style={h.row}>
    <GuideAvatar />
    <View style={h.copy}>
      <Text accessibilityRole="header" numberOfLines={1} style={h.title}>{t('guide.title')}</Text>
      <Text numberOfLines={1} style={h.subtitle}>{t('guide.subtitle')}</Text>
    </View>
    {onClear && <CircleButton accessibilityLabel={t('guide.clear')} disabled={clearDisabled} icon="trash" onPress={onClear} size={44} tone="tint" />}
  </View>;
}

const h = StyleSheet.create({
  avatar: { alignItems: 'center', justifyContent: 'center' },
  avatarRing: { backgroundColor: colors.skyWash },
  copy: { flex: 1, minWidth: 0 },
  row: { alignItems: 'center', flexDirection: 'row', gap: 12, paddingBottom: 12 },
  subtitle: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 15, lineHeight: 20 },
  title: { color: colors.ink, fontFamily: fonts.bold, fontSize: 24, letterSpacing: -0.4, lineHeight: 30 },
});

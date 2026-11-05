import { useTranslation } from 'react-i18next';
import { StyleSheet, Text, View } from 'react-native';

import { CircleButton, Icon } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { fonts, typography } from '../../../theme/typography';

/** Muted text on the warm tint (5.9:1 on surfaceTint, 6.4:1 on canvas). Kept as an alias for Guide surfaces. */
export const washMuted = colors.textMuted;

/** Guide avatar: flat warm tile with a lantern (a local guide, not an AI sparkle). Decorative. */
export function GuideAvatar({ size = 48 }: { size?: number }) {
  return <View
    accessibilityElementsHidden
    importantForAccessibility="no-hide-descendants"
    style={[h.avatar, { borderRadius: size / 2, height: size, width: size }]}
  >
    <Icon color={colors.accentText} name="lantern" size={Math.round(size * 0.55)} />
  </View>;
}

/** SCR-034 header: eyebrow "Trả lời từ nguồn đã kiểm duyệt", title "Hỏi đáp địa điểm" and (in a chat) the clear button. */
export function GuideHeader({ onClear, clearDisabled }: { onClear?: () => void; clearDisabled?: boolean }) {
  const { t } = useTranslation();
  return <View style={h.row}>
    <View style={h.copy}>
      <Text numberOfLines={1} style={typography.eyebrow}>{t('guide.eyebrow')}</Text>
      <Text accessibilityRole="header" numberOfLines={1} style={h.title}>{t('guide.title')}</Text>
      <Text numberOfLines={1} style={h.subtitle}>{t('guide.subtitle')}</Text>
    </View>
    {onClear && <CircleButton accessibilityLabel={t('guide.clear')} disabled={clearDisabled} icon="trash" onPress={onClear} size={44} tone="tint" />}
  </View>;
}

const h = StyleSheet.create({
  avatar: { alignItems: 'center', backgroundColor: colors.surfaceTint, justifyContent: 'center' },
  copy: { flex: 1, minWidth: 0 },
  row: { alignItems: 'center', flexDirection: 'row', gap: 12, paddingBottom: 12 },
  subtitle: { color: colors.textMuted, fontFamily: fonts.regular, fontSize: 15, lineHeight: 20 },
  title: { color: colors.ink, fontFamily: fonts.bold, fontSize: 24, letterSpacing: -0.4, lineHeight: 30, marginTop: 4 },
});

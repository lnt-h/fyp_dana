import { useTranslation } from 'react-i18next';
import { StyleSheet, Text, View } from 'react-native';

import { colors } from '../../../theme/colors';
import { typography } from '../../../theme/typography';
import { dayPartNow } from './homeSheetUtils';

/** "Chào buổi sáng, {first name} 👋" by the hour in Asia/Ho_Chi_Minh; guests get "Chào bạn 👋". */
export function Greeting({ name, cityName }: { name: string | null; cityName: string }) {
  const { t } = useTranslation();
  const firstName = name?.trim().split(/\s+/)[0] ?? '';
  const part = dayPartNow();
  const title = firstName
    ? part === 'morning'
      ? t('homeSheet.greeting.morning', { name: firstName })
      : part === 'afternoon'
        ? t('homeSheet.greeting.afternoon', { name: firstName })
        : t('homeSheet.greeting.evening', { name: firstName })
    : t('homeSheet.greeting.guest');
  return (
    <View>
      <Text accessibilityRole="header" numberOfLines={2} style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>
        {cityName ? t('homeSheet.greeting.subtitle', { city: cityName }) : t('homeSheet.greeting.subtitleNoCity')}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  subtitle: { ...typography.body, color: colors.textMuted, fontSize: 15, marginTop: 2 },
  title: { ...typography.title, color: colors.deepOcean, fontSize: 26, lineHeight: 32 },
});

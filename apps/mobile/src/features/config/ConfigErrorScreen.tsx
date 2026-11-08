import { StatusBar } from 'expo-status-bar';
import { useTranslation } from 'react-i18next';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Icon } from '../../components/ui/Icon';
import { colors } from '../../theme/colors';
import { spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';

/**
 * Shown by the root layout instead of the app when `EXPO_PUBLIC_API_URL` is missing or invalid (config.ts). The app has
 * no local data, so there is nothing to fall back to. Copy is in the current locale (`common.configError`, VI + EN).
 */
export function ConfigErrorScreen() {
  const { t } = useTranslation();
  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar style="light" />
      <ScrollView contentContainerStyle={styles.content}>
        <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.icon}>
          <Icon color={colors.white} name="warning" size={32} />
        </View>
        <Text accessibilityRole="header" style={styles.title}>{t('common.configError.title')}</Text>
        <Text style={styles.body}>{t('common.configError.body')}</Text>
        <Text selectable style={styles.fix}>{t('common.configError.fix')}</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { backgroundColor: colors.deepOcean, flex: 1 },
  content: { flexGrow: 1, gap: spacing.md, justifyContent: 'center', padding: spacing.xl },
  icon: { alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.12)', borderRadius: 32, height: 64, justifyContent: 'center', width: 64 },
  title: { ...typography.title, color: colors.white },
  body: { ...typography.body, color: colors.white },
  fix: { color: 'rgba(255,255,255,0.8)', fontFamily: fonts.regular, fontSize: 14, lineHeight: 20 },
});

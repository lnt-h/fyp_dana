import { StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { colors } from '../../../theme/colors';
import { PrimaryButton, SparkleIcon } from './PlannerUI';

/** SCR-008 Plan card inside the Home bottom sheet: entry to SCR-022. Laid out in the Home design-frame scale. */
export function PlanCard({ cityName, scale, onPress }: { cityName: string; scale: number; onPress: () => void }) {
  const { t } = useTranslation();
  return <View style={[styles.card, { marginHorizontal: 20 * scale, marginTop: 34 * scale, padding: 18 * scale }]}>
    <View style={styles.top}>
      <View style={styles.tile}><SparkleIcon /></View>
      <View style={styles.copy}>
        <Text style={styles.title}>{t('planner.home.title', { city: cityName })}</Text>
        <Text style={styles.subtitle}>{t('planner.home.subtitle')}</Text>
      </View>
    </View>
    <PrimaryButton label={t('planner.home.action')} onPress={onPress} />
  </View>;
}

const styles = StyleSheet.create({
  card: { borderRadius: 24, backgroundColor: colors.skyWash, gap: 16 },
  top: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  tile: { width: 42, height: 42, borderRadius: 14, backgroundColor: colors.white, alignItems: 'center', justifyContent: 'center' },
  copy: { flex: 1 },
  title: { fontFamily: 'HankenGrotesk_700Bold', fontSize: 18, lineHeight: 23, color: colors.deepOcean, letterSpacing: -0.3 },
  subtitle: { fontFamily: 'HankenGrotesk_500Medium', fontSize: 14, lineHeight: 20, color: colors.textMuted, marginTop: 2 },
});

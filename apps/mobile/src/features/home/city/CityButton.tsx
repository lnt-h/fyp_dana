import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { elevation } from '../../../theme/elevation';
import { fonts } from '../../../theme/typography';

type Props = {
  /** City name in the UI language, or null while the city list loads. */
  cityName: string | null;
  onPress: () => void;
};

/** "📍 {city}, Việt Nam ⌄" pill over the map; opens the city sheet (SCR-020). */
export function CityButton({ cityName, onPress }: Props) {
  const { t } = useTranslation();
  const name = cityName ?? '…';
  return (
    <Pressable
      accessibilityLabel={t('home.city.buttonLabel', { city: name })}
      accessibilityRole="button"
      hitSlop={4}
      onPress={onPress}
      style={({ pressed }) => [styles.pill, elevation.sm, pressed && styles.pressed]}
    >
      <Icon color={colors.tealText} name="map-pin" size={18} />
      <Text numberOfLines={1} style={styles.text}>{t('home.city.button', { city: name, country: t('common.country') })}</Text>
      <View style={styles.chevron}>
        <Icon color={colors.ink} name="chevron-right" size={16} strokeWidth={2.2} />
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chevron: { transform: [{ rotate: '90deg' }] },
  pill: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255,255,255,0.94)',
    borderRadius: 22,
    flexDirection: 'row',
    gap: 6,
    height: 44,
    maxWidth: '100%',
    paddingHorizontal: 14,
  },
  pressed: { opacity: 0.85 },
  text: { color: colors.ink, flexShrink: 1, fontFamily: fonts.bold, fontSize: 15, lineHeight: 20 },
});

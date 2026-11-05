import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { interestOptions, travelTypes, type Interest, type TravelType } from './AccountContext';
import { colors } from '../../theme/colors';
import { radii, spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';

const photos = {
  Culture: require('../../../assets/images/places/cham-sculpture.png'),
  Beach: require('../../../assets/images/places/beach.png'),
  Food: require('../../../assets/images/places/mi-quang.png'),
  Nature: require('../../../assets/images/places/linh-ung-pagoda.png'),
};
export function TravelPreferences({ selected, onSelect, travelType, onTravelType }: {
  selected: Interest[]; onSelect: (value: Interest[]) => void;
  travelType?: TravelType; onTravelType: (value: TravelType) => void;
}) {
  const { t } = useTranslation();
  return <>
    <Text style={styles.section}>{t('account.preferences.interested')}</Text>
    <Text style={styles.hint}>{t('account.preferences.interestedHint')}</Text>
    <View style={styles.grid}>{interestOptions.map(label => {
      const checked = selected.includes(label);
      return <Pressable key={label} accessibilityRole="checkbox" accessibilityLabel={t(`account.preferences.interests.${label}`)} accessibilityState={{ checked }} aria-checked={checked}
        onPress={() => onSelect(checked ? selected.filter(value => value !== label) : [...selected, label])} style={styles.tile}>
        <View style={[styles.frame, checked && styles.selected]}>
          <Image source={photos[label]} resizeMode="cover" style={styles.photo} />
          {checked && <View style={styles.check}><Text style={styles.tick}>✓</Text></View>}
        </View>
        <Text style={styles.label}>{t(`account.preferences.interests.${label}`)}</Text>
      </Pressable>;
    })}</View>
    <Text style={styles.section}>{t('account.preferences.travelType')}</Text>
    <Text style={styles.hint}>{t('account.preferences.travelTypeHint')}</Text>
    <View style={styles.types}>{travelTypes.map(type => <Pressable key={type} accessibilityRole="radio" accessibilityLabel={t(`account.preferences.travelTypes.${type}`)}
      accessibilityState={{ checked: type === travelType }} aria-checked={type === travelType} onPress={() => onTravelType(type)}
      style={[styles.chip, type === travelType && styles.chipSelected]}>
      <Text style={[styles.label, type === travelType && styles.light]}>{t(`account.preferences.travelTypes.${type}`)}</Text>
    </Pressable>)}</View>
  </>;
}
const styles = StyleSheet.create({
  section: { ...typography.headline, color: colors.ink, marginTop: spacing.xs },
  hint: { ...typography.caption, fontSize: 14, lineHeight: 20, marginTop: spacing.xxs, marginBottom: spacing.md },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: spacing.md, marginBottom: spacing.xl },
  tile: { width: '48%' },
  frame: { width: '100%', aspectRatio: 1.5, borderWidth: 3, borderColor: 'transparent', borderRadius: radii.card, overflow: 'hidden' },
  selected: { borderColor: colors.audioTeal },
  photo: { position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', borderRadius: radii.card - 3 },
  label: { fontFamily: fonts.bold, fontSize: 15, color: colors.ink, textAlign: 'center', marginVertical: 6 },
  check: { position: 'absolute', top: 8, right: 8, width: 28, height: 28, borderRadius: 14, backgroundColor: colors.audioTeal, borderWidth: 2, borderColor: colors.white, alignItems: 'center', justifyContent: 'center' },
  tick: { color: colors.white, fontSize: 15, fontFamily: fonts.bold },
  types: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginBottom: spacing.lg },
  chip: { paddingHorizontal: spacing.md, minHeight: 46, borderRadius: radii.chip, borderWidth: 1.5, borderColor: '#DCE8EE', justifyContent: 'center', backgroundColor: colors.white },
  chipSelected: { backgroundColor: colors.tealText, borderColor: colors.tealText },
  light: { color: colors.white },
});

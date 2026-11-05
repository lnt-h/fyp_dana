import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { interestOptions, travelTypes, type Interest, type TravelType } from './AccountContext';
import { palette } from '../auth/components/AuthUI';

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
  section: { fontFamily: 'HankenGrotesk_700Bold', fontSize: 19, color: palette.deepOcean, marginTop: 8 },
  hint: { fontSize: 14, lineHeight: 20, color: palette.muted, marginTop: 4, marginBottom: 14 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: 16, marginBottom: 20 },
  tile: { width: '48%' },
  frame: { width: '100%', aspectRatio: 1.5, borderWidth: 3, borderColor: 'transparent', borderRadius: 20, overflow: 'hidden' },
  selected: { borderColor: palette.audioTeal },
  photo: { position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', borderRadius: 17 },
  label: { fontFamily: 'HankenGrotesk_700Bold', fontSize: 15, color: palette.deepOcean, textAlign: 'center', marginVertical: 6 },
  check: { position: 'absolute', top: 7, right: 7, width: 26, height: 26, borderRadius: 13, backgroundColor: palette.audioTeal, alignItems: 'center', justifyContent: 'center' },
  tick: { color: palette.white, fontSize: 18, fontWeight: '700' },
  types: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 18 },
  chip: { paddingHorizontal: 15, minHeight: 46, borderRadius: 16, borderWidth: 1.5, borderColor: palette.border, justifyContent: 'center', backgroundColor: palette.white },
  chipSelected: { backgroundColor: palette.tealText, borderColor: palette.tealText },
  light: { color: palette.white },
});

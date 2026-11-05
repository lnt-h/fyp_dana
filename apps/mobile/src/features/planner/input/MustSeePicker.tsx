import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, FlatList, Modal, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { palette } from '../../auth/components/AuthUI';
import { useReducedMotion } from '../../../hooks/useReducedMotion';
import { searchPlaces } from '../../../lib/api/source';
import type { Place, Uuid } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { p } from './PlannerUI';

export const MUST_SEE_MAX = 10;
type Chosen = Pick<Place, 'id' | 'name'>;

/** Must-see picker (SCR-028 picker mode, simplified): published places of the trip's city only (API-010), max 10. */
export function MustSeePicker({ visible, cityId, cityName, selected, onChange, onClose }: {
  visible: boolean; cityId: Uuid; cityName: string; selected: Chosen[]; onChange: (next: Chosen[]) => void; onClose: () => void;
}) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const reduceMotion = useReducedMotion();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Place[] | null>(null);
  const [failed, setFailed] = useState(false);
  const requestId = useRef(0);

  useEffect(() => {
    if (!visible) return;
    const id = ++requestId.current;
    setFailed(false);
    const timer = setTimeout(() => {
      searchPlaces(cityId, query.trim() || undefined)
        .then(items => { if (id === requestId.current) setResults(items); })
        .catch(() => { if (id === requestId.current) { setResults([]); setFailed(true); } });
    }, 250);
    return () => clearTimeout(timer);
  }, [cityId, query, visible]);

  const full = selected.length >= MUST_SEE_MAX;
  const toggle = (place: Place) => {
    const isChosen = selected.some(item => item.id === place.id);
    if (isChosen) onChange(selected.filter(item => item.id !== place.id));
    else if (!full) onChange([...selected, { id: place.id, name: place.name }]);
  };

  return <Modal transparent visible={visible} animationType={reduceMotion ? 'none' : 'slide'} onRequestClose={onClose}>
    <View style={p.backdrop}>
      <Pressable accessibilityElementsHidden importantForAccessibility="no" onPress={onClose} style={StyleSheet.absoluteFill} />
      <View accessibilityViewIsModal style={[p.sheet, styles.sheet, { paddingBottom: insets.bottom + 12 }]}>
        <View style={p.sheetHeader}>
          <Text accessibilityRole="header" style={p.sheetTitle}>{t('planner.mustSee.title', { city: cityName })}</Text>
          <Pressable accessibilityRole="button" accessibilityLabel={t('planner.mustSee.close')} onPress={onClose} style={p.touch}>
            <Text style={p.link}>{t('planner.date.done')}</Text>
          </Pressable>
        </View>
        <Text accessibilityLiveRegion="polite" style={[p.hint, { marginBottom: 10 }]}>{full ? t('planner.mustSee.max') : t('planner.mustSee.count', { count: selected.length })}</Text>
        <View style={[p.field, { minHeight: 52 }]}>
          <TextInput value={query} onChangeText={setQuery} accessibilityLabel={t('planner.mustSee.searchLabel')} placeholder={t('planner.mustSee.searchPlaceholder')}
            placeholderTextColor={colors.textMuted} maxLength={120} autoCorrect={false} returnKeyType="search" style={styles.input} />
        </View>
        {results === null
          ? <View style={styles.status}><ActivityIndicator color={colors.audioTeal} /><Text style={p.hint}>{t('planner.mustSee.loading')}</Text></View>
          : <FlatList data={results} keyExtractor={item => item.id} keyboardShouldPersistTaps="handled" style={styles.list}
            ListEmptyComponent={<Text accessibilityLiveRegion="polite" style={[p.hint, styles.status]}>{failed ? t('planner.errors.codes.network') : t('planner.mustSee.empty')}</Text>}
            renderItem={({ item }) => {
              const checked = selected.some(chosen => chosen.id === item.id);
              const disabled = !checked && full;
              const secondary = item.name_vi !== item.name ? item.name_vi : null;
              return <Pressable accessibilityRole="checkbox" accessibilityState={{ checked, disabled }} disabled={disabled}
                accessibilityLabel={[item.name, secondary].filter(Boolean).join(', ')} onPress={() => toggle(item)}
                style={({ pressed }) => [styles.row, (pressed || disabled) && { opacity: 0.55 }]}>
                <View style={[styles.box, checked && styles.boxChecked]}>{checked && <Text style={p.chipTick}>✓</Text>}</View>
                <View style={p.flex}>
                  <Text style={styles.name}>{item.name}</Text>
                  {secondary && <Text style={styles.secondary}>{secondary}</Text>}
                </View>
                {checked && <Text style={styles.added}>{t('planner.mustSee.added')}</Text>}
              </Pressable>;
            }} />}
      </View>
    </View>
  </Modal>;
}

const styles = StyleSheet.create({
  sheet: { maxHeight: '85%', minHeight: '60%' },
  input: { flex: 1, fontSize: 16, color: colors.deepOcean, paddingVertical: 12 },
  list: { marginTop: 8 },
  status: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 20 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 14, minHeight: 60, paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: colors.hairline },
  box: { width: 26, height: 26, borderRadius: 8, borderWidth: 1.5, borderColor: palette.border, alignItems: 'center', justifyContent: 'center' },
  boxChecked: { backgroundColor: colors.tealText, borderColor: colors.tealText },
  name: { fontFamily: 'HankenGrotesk_700Bold', fontSize: 16, color: colors.deepOcean },
  secondary: { fontFamily: 'HankenGrotesk_500Medium', fontSize: 14, color: colors.textMuted, marginTop: 2 },
  added: { fontFamily: 'HankenGrotesk_700Bold', fontSize: 13, color: colors.tealText },
});

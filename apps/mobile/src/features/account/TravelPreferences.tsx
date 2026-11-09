import { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Chip, categoryIcon } from '../../components/ui';
import { currentLocale } from '../../i18n';
import { listCategories } from '../../lib/api/source';
import type { Category } from '../../lib/api/types';
import { categoryColor, colors } from '../../theme/colors';
import { radii, spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { travelTypes, type TravelType } from './AccountContext';

/** Server cap for `interest_category_codes` (API-005). */
export const MAX_INTEREST_CODES = 20;

/**
 * Travel preferences (Wave 5 P1): every catalog category from API-009 as checkbox chips — the same
 * 12 categories, names and icons the planner wizard shows — plus the travel-type radios (profile
 * data, never sent to the planner). Selection is category codes; the screen maps the four legacy
 * profile interests at its boundary.
 */
export function TravelPreferences({ selected, onSelect, travelType, onTravelType }: {
  selected: string[]; onSelect: (value: string[]) => void;
  travelType?: TravelType; onTravelType: (value: TravelType) => void;
}) {
  const { t } = useTranslation();
  const vi = currentLocale() === 'vi';
  const [categories, setCategories] = useState<Category[] | null>(null);
  useEffect(() => {
    let alive = true;
    listCategories()
      .then(items => { if (alive) setCategories([...items].sort((a, b) => a.sort_order - b.sort_order)); })
      .catch(() => { if (alive) setCategories([]); });
    return () => { alive = false; };
  }, []);

  function toggle(code: string) {
    const checked = selected.includes(code);
    if (checked) onSelect(selected.filter(item => item !== code));
    else if (selected.length < MAX_INTEREST_CODES) onSelect([...selected, code]);
  }

  return <>
    <Text style={styles.section}>{t('account.preferences.interested')}</Text>
    <Text style={styles.hint}>{t('account.preferences.interestedHint')}</Text>
    {categories === null ? <Text style={styles.hint}>{t('planner.interests.loading')}</Text>
      : <View style={styles.chips}>{categories.map(category => {
        const checked = selected.includes(category.code);
        return <Chip
          key={category.code}
          icon={categoryIcon(category.code)}
          tone={categoryColor(category.code)}
          label={vi ? category.name_vi : category.name_en}
          selected={checked}
          disabled={!checked && selected.length >= MAX_INTEREST_CODES}
          onPress={() => toggle(category.code)}
        />;
      })}</View>}
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
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: spacing.xl },
  label: { fontFamily: fonts.bold, fontSize: 15, color: colors.ink, textAlign: 'center', marginVertical: 6 },
  types: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginBottom: spacing.lg },
  chip: { paddingHorizontal: spacing.md, minHeight: 46, borderRadius: radii.chip, borderWidth: 1.5, borderColor: colors.hairline, justifyContent: 'center', backgroundColor: colors.white },
  chipSelected: { backgroundColor: colors.tealText, borderColor: colors.tealText },
  light: { color: colors.white },
});
